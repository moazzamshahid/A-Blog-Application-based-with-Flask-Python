from email.message import Message
from flask import Flask, render_template, request, session, redirect
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename
import math

with open("config.json","r") as c:
    params=json.load(c)["Params"]

app= Flask(__name__)
app.secret_key = "super secret key"
app.config.update(
    MAIL_SERVER= "smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail-user"],
    MAIL_PASSWORD=params["gmail-password"]

)
app.config["Upload_Folder"]=params["upload_location"]
mail=Mail(app)


if params["local_server"]==True:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_Uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["Prod_Uri"]
db = SQLAlchemy(app)
class Contact(db.Model):
    ''' The variables should match exacty like names of columns in table'''
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(70), nullable=False)
    Phone_no = db.Column(db.String(70), nullable=False)
    Message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(70), nullable=False)
    Email_id = db.Column(db.String(70), nullable=False)

class post(db.Model):
    ''' The variables should match exacty like names of columns in table'''
    id = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(120), nullable=False)
    Slug = db.Column(db.String(120), nullable=False)
    Post_by = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(70), nullable=False)
    Content = db.Column(db.String(300), nullable=False)
    img_file = db.Column(db.String(300), nullable=False)





@app.route("/")
def index():
    posts= post.query.filter_by().all()
    last=math.ceil(len(posts)/int(params["no_of_Posts"])) 
    print(last)
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    else:
        page = int(page)
    posts=posts[(page-1)*int(params["no_of_Posts"]):(page-1)*int(params["no_of_Posts"])+int(params["no_of_Posts"])]
    if page==1:
        prev= "#"
        next="/?page="+ str(page+1)
    elif page==last:
        prev= "/?page="+ str(page-1)
        next= "#" 
    else:
        next="/?page="+ str(page+1)
        prev= "/?page="+ str(page-1)

    return render_template("index.html", params=params,posts=posts, next=next, prev=prev)

@app.route("/about")
def about():
    return render_template("about.html",params=params)


@app.route("/contact", methods=['GET','POST'])
def contact():
    if (request.method=='POST'):
        Name=request.form.get("name")
        phone=request.form.get("phone")
        msg=request.form.get("msg")
        email=request.form.get("email")
        date= datetime.now()
        # LHS is from class variables and RHS is from local function
        entry=Contact(Name=Name,Phone_no=phone,Message=msg,  date=date,Email_id=email)
        db.session.add(entry)
        db.session.commit()
       ## mail.send_message("New message from blog",
       ##  sender=email, recipients=[params["gmail-user"]],
       ##  body=msg + "\n" + phone
       ##  )    

    return render_template("contact.html",params=params)

@app.route("/edit/<string:Id>", methods=["GET","POST"] )
def edit(Id):
    if ("user" in session and session["user"] == params["admin_user"]):  
        if request.method == "POST":
            box_Title=request.form.get("Title") 
            box_Slug=request.form.get("Slug")
            box_Content=request.form.get("Content")
            box_file=request.form.get("img_file")
            box_post_by=request.form.get("post_by")

            Posts=post.query.filter_by(id=Id).first()
            Posts.Title=box_Title
            Posts.Slug=box_Slug
            Posts.Content=box_Content
            Posts.Post_by=box_post_by
            Posts.img_file=box_file
            db.session.commit()
            return redirect("/edit/"+Id)
           
        Posts=post.query.filter_by(id=Id).first()
        return render_template("edit.html", params=params, Post=Posts)
    else:
        return render_template("login.html", params=params)

@app.route("/edit/0", methods=["GET","POST"])
def Add_Post():
    if ("user" in session and session["user"]==params["admin_user"] ):
        if request.method=="POST":   
            box_Title=request.form.get("Title") 
            box_Slug=request.form.get("Slug")
            box_Content=request.form.get("Content")
            box_file=request.form.get("img_file")
            box_post_by=request.form.get("post_by")
            box_date=datetime.now()
            Posts=post(Title=box_Title,Slug=box_Slug,Post_by=box_post_by,img_file=box_file,Content=box_Content,date=box_date)
            db.session.add(Posts)
            db.session.commit()
        return render_template("add_post.html", params=params)
    else:
        return render_template("login.html", params=params)

@app.route("/logout")
def logout():
    session.pop("user")
    return redirect("/dashboard")

@app.route("/delete/<string:id>", methods=["GET","POST"])
def delete_post(id):
    if ("user" in session and session["user"] == params["admin_user"]):
        Post=post.query.filter_by(id=id).first()
        db.session.delete(Post)
        db.session.commit()
    return redirect("/dashboard")
    


@app.route("/post")
def Post():
    return render_template("post.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    
    if ("user" in session and session["user"] == params["admin_user"]):
        posts=post.query.all()
        return render_template("dashboard.html", params=params, posts=posts) 
    if request.method=="POST":
        User_name=request.form.get("uname")
        password=request.form.get("password")
        if User_name==params["admin_user"] and password == params["admin_password"]:
            session["user"]= User_name
            posts=post.query.all()
            return render_template("dashboard.html", params=params, posts=posts)
    # redirect to admin panel
    return render_template("login.html", params=params)


@app.route("/post/<string:post_slug>",methods=["GET"])
def post_route(post_slug):
    Post_ = post.query.filter_by(Slug=post_slug).first()
    print(Post_.Title)
    return render_template("post.html",params=params, post=Post_)

@app.route("/file_uploader", methods=["GET","POST"])
def uploader():
    if ("user" in session and session["user"] == params["admin_user"]):
        if request.method=="POST":
            f=request.files["myfile"]
            f.save(os.path.join(app.config["Upload_Folder"],secure_filename(f.filename)))
            return "Uploaded Successfully"



app.run(debug=True)
