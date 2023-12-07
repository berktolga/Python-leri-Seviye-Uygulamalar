from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from email_validator import validate_email, EmailNotValidError
from functools import wraps

#Kullanıcı Kayıt Formu Class'ı
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.length(min=5,max=30)])
    username = StringField("Kullanıcı Adı", validators=[validators.length(min = 5, max = 30)])
    email = StringField("E-mail Adresi", validators=[validators.email(message="Lütfen Geçerli Bir E-mail Adresi Giriniz!")])
    password = PasswordField("Parola", validators=[
        validators.DataRequired(message= "Lütfen bir parola giriniz."), 
        validators.EqualTo(fieldname="confirm",message="Parolanız Aynı Değil!")
    ])
    confirm = PasswordField("Parola Doğrula")
    
#Kullanıcı Giriş Formu Class'ı
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

#Makale Form Class'ı
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min = 5, max = 100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min = 10)])


#Kullanıcı Giriş Decorator'ı
#Kullanıcı giriş yapmadan bir sayfaya gitmesini engellemek için yapıyoruz.
def login_required(f):#f yerine bir fonksiyon gelecek ve biz onu kontrol etmiş olacağız.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:#Session'ın içerisinde logged_in diye bir anahtar değer var mı yok mu onu kontrol ediyoruz.True gelirse giriş yapılmış demektir.
            return f(*args, **kwargs) #Fonksiyonu (yani f'i veya f yeribe gelen fonksiyonu) çalıştırırız.
        else:#Diğer durumda giriş yapılmamıştır ve direkt anasayfaya yönlendirme yaparız.
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function

app = Flask(__name__)#Flask sınıfından bir tane obje oluşturuyoruz.
#Her bir url adresi isteğine karşılık Flask'ta bir tane fonksiyon bulunuyor. Flask'ta hazır bir decorator mantığını kullanacağız

app.secret_key="ybblog" #Flash mesajlarının çalışabilmesi için bir tane kendimiz secretkey belirliyoruz.

#Veri tabanı işlemleri(Flask ile MYSQL ilişkisini kurmuş oluyoruz.)
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor" #MYSQL veritabanında 'sözlük yapısında'n bilgileri alabilmek için 

#MYSQL'i kullanabilmek için import edilen MYSQL sınıfından bir tane obje oluşturmamız gerekiyor.
mysql = MySQL(app)

@app.route("/")#Bu her url adresi istediğimiz zaman kullanılabilen bir decorator. Request'i root("/" ile) olarak yapıyoruz.
def index():#Python'da decorator'ların altına yazılan fonksiyon o decorator'a göre çalışır.
    articles = [
        {"id":1,"title":"Deneme1","content":"Deneme1 içerik"},
        {"id":2,"title":"Deneme2","content":"Deneme2 içerik"},
    ]
    return render_template("index.html", articles = articles)
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/article/<string:id>")#Dinamik url yapısı: id'nin bir tane string olduğunu ve id değişkeninde tutulduğunu görebiliriz.
def detail(id):
    return "Article Id:" + id
@app.route("/register",methods = ["GET","POST"])#Bu url'nin hem get hem de post request alabilir olduğunu belirtti.s
def register():
    form = RegisterForm(request.form)#Yukarıdaki RegisterForm class'ından bir tane obje oluşturuyoruz. Post ile formu alabilmemiz için dahil ettiğimiz request'in formunu içeride almalıyız.

    if request.method == "POST" and form.validate():# Post methodu yapılmış ve formumuz validate ise formda yazılan bilgileri çekiyoruz.
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) 

        cursor = mysql.connection.cursor()#import edilen MYSQL sınıfından bir tane obje oluşturmuştuk. Şimdi onu kullanarak veri tabanında gezinip işlem yapmak için bir tane cursor oluşturuyoruz.
        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)" #Veri tabanı için sorgu yazdık.
        cursor.execute(sorgu,(name,email,username,password))#Sorguyu veri tabanında çalıştırıyoruz. Ayrıca %s'leri belirtmek için bir demet kullanıyoruz. Eğer tek bir değer demet ile yazılacaksa '(name,)' şeklinde virgülle yazılmalı.
        mysql.connection.commit()# Değişikliği veri tabanına gönderiyoruz.
        cursor.close()#Veri tabanı işlemi bittikten sonra veri tabanı ile bağlantıyı kapatıyoruz.

        flash("Başarıyla Kayıt Oldunuz.","success")

        return redirect(url_for("login"))#*Fonksiyonun ismine göre url adresine gitmek istediğimizi söyleyebiliriz.* İndex fonksiyonuyla ilişkili url'e gidecek.
    else:#Get request olduğunu anlamış oluruz.   
        return render_template("register.html",form = form) #Form = form ile formu görüntülemeye çalışıyoruz.
    
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data#Formda girilen bilgileri alıyoruz.
        password_entered = form.password.data

        cursor = mysql.connection.cursor() 
        sorgu = "Select * From users where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()#Kullanıcının tüm bilgilerini veri tabanından alıyoruz.
            real_password = data["password"]#Gerçek parolayı aldık.
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yapıldı.","success")
                session["logged_in"] = True #Siteye giriş yaptıktan sonra oturum açılma kısmı
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parola yanlış girildi.","dagerous")
                return redirect(url_for("login"))
        else:
            flash("Kullanıcı adı kayıtlı değil.","danger")
            return redirect(url_for("login"))
    return render_template("login.html", form = form)

@app.route("/logout")
def logout():
    session.clear() #Siteden çıkış yapıldıktan sonra oturum kapatma kısmı
    return redirect(url_for("index"))

@app.route("/dashboard")#Kontrol Paneli için
@login_required#Yukarıda yazdığımız decorator'ı burada kullanıyoruz.
def dashboard():
    #Kontrol panelinde sadece giriş yapan kullanıcının makalelerini göstermek için:
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")

#Makale Ekleme
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form) #Yukarıda yazdığımız makale formu class'ından bir obje oluşturuyoruz.
    if request.method == "POST" and form.validate():#Gelen requestin GET mi POST mu olduğunu kontrol etmeliyiz.
        title = form.title.data
        content = form.content.data
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles (title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarıyla eklendi.","success")
        return redirect(url_for("dashboard"))
    else:
        return render_template("addarticle.html",form = form)

#Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"
    result = cursor.execute(sorgu)
    if result > 0:
        articles = cursor.fetchall()#Veri tabanındaki bütün makaleler liste içerisinde sözlük olarak gelecek.
        return render_template("articles.html", articles = articles)#Gelen makaleleri 'articles' yardımıyla makaleler sayfasında görüntüleriz
    else:
        return render_template("articles.html")

#Detay Sayfası
@app.route("/articledetail/<string:id>")
def articledetail(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        articledetail = cursor.fetchone()
        return render_template("articledetail.html", articledetail = articledetail)
    else:
        return render_template("articledetail.html")

#Makale Silme
@app.route("/delete/<string:id>")#Dinamil url yapısı
@login_required#Yukarıda yazdığımız decorator'ı kullandık. Giriş yapmayan kullanıcı silme işlemi yapmak isterse giriş yap kısmına yönlendirecek.
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s and id = %s" #Önce Kullanıcının giriş yapan kullanıcı olup olmadığını kontrol eidyoruz.
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "Delete from articles where id = %s" #Eğer kullanıcı giriş yapan kullanıcı ise makaleyi silecek
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()#Veri tabanında değişiklik yapıldığında kullanılmalı.
        flash("Silme işlemi başarılı!","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok.","danger")
        return redirect(url_for("index"))


#Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"] )
@login_required
def update(id):
    if request.method == "GET":#GET Request - Yani veri tabanındaki kayıtlı bilgileri getirmek
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:#Makalenin bize ait olmaması durumu ve makalenin hiç olmaması durumu
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok!","danger")
            return redirect(url_for("index"))
        else:
            article_now = cursor.fetchone()
            form = ArticleForm()#Formu normalde request.form ile yazıyorduk. Ancak şimdi formu daha önce kaydedilmiş haliyle getirmemiz gerekiyor.
            form.title.data = article_now["title"]#Formun başlığının içeriğine veri tabanından gelen başlığı atıyoruz.
            form.content.data = article_now["content"]
            return render_template("update.html", form = form)
    else:# POST Request - Güncellenen halini veri tabanına göndermek
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale başarıyla güncellendi.","success")
        return redirect(url_for("dashboard"))

#Bir web sunucusunu çalıştıracağız
if __name__ == "__main__":#Python dosyası terminalden mi çalıştırılmış yoksa bir python modülü olarak mı aktarılmış onu anlamamızı sağlıyor.
    app.run(debug=True)# Web sunucusunu çalıştırıyoruz.(Localhostta)










