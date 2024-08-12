import  re
from flask import jsonify
import uuid
from flask import Flask 
from flask import render_template, request, url_for,redirect, session, abort, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.utils import secure_filename
import matplotlib
matplotlib.use('Agg')
from sqlalchemy.orm import relationship, backref
from matplotlib import pyplot as plt
import os
from flask import Flask, render_template
from flask_restful import reqparse,Resource,Api
from flask_security import UserMixin, RoleMixin,Security,current_user,SQLAlchemySessionUserDatastore,login_required,roles_required,login_user

# from transformers import pipeline
import ollama


curr_dir=os.path.abspath(os.path.dirname(__file__))

#Creating a Flask instance
app=Flask(__name__, template_folder="templates")
app.secret_key="Team_8"


#adding the database
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(curr_dir,'SEEK.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

#setting uploading types of images & the folder to upload images
app.config['UPLOAD_EXTENSIONS']=['.jpg', '.png', '.jpeg']
app.config['UPLOAD_PATH']='static\images'


from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()
api = Api(app)
app.app_context().push()

#___________________________models___________________________________________
class Admin(db.Model):
    __tablename__="admin"
    admin_id=db.Column(db.Integer, primary_key=True, nullable=False)
    ad_fname=db.Column(db.String(30), nullable=False)
    ad_lname=db.Column(db.String(30))
    ad_email=db.Column(db.String(30), nullable=False)
    ad_username=db.Column(db.String(20), nullable=False, unique=True)
    ad_pwd=db.Column(db.String(20), nullable=False)


class contents(db.Model):
    __tablename__ = "contents"
    content_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content_name = db.Column(db.String(30), nullable=False)
    content_link = db.Column(db.String(50), nullable=False)
    content_transcript = db.Column(db.String(1000), nullable=False)
    content_course_id = db.Column(db.Integer, nullable=False)
    related_prompts = relationship("prompts", cascade="all, delete", backref=backref("content", cascade="all, delete"))

class prompts(db.Model):
    __tablename__ = "prompts"
    prompt_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    puser_id = db.Column(db.Integer, nullable=False)
    pcontent_id = db.Column(db.Integer, db.ForeignKey('contents.content_id', ondelete='CASCADE'), nullable=False)
    ptranscript = db.Column(db.Text, nullable=False)
    pprompt = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)

class MCQAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_name = db.Column(db.String(30), nullable=False)
    question = db.Column(db.String(255), nullable=False)
    option_a = db.Column(db.String(100), nullable=False)
    option_b = db.Column(db.String(100), nullable=False)
    option_c = db.Column(db.String(100), nullable=False)
    option_d = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.course_id'), nullable=False)

class Coding(db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    coding_question = db.Column(db.String(255))
    content_name = db.Column(db.String(30), nullable=False)

class Subjective(db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    subjective_question = db.Column(db.String(255))
    content_name = db.Column(db.String(30), nullable=False)    

class Users(db.Model):
    __tablename__="users"
    user_id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    user_fname=db.Column(db.String(30), nullable=False)
    user_lname=db.Column(db.String(30))
    user_email=db.Column(db.String(30), nullable=False)
    user_username=db.Column(db.String(20), nullable=False, unique=True)
    user_pwd=db.Column(db.String(20), nullable=False)


class course(db.Model):
    __tablename__="course"
    course_id=db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    course_name=db.Column(db.String(30), nullable=False)
    course_details = db.Column(db.String(100), nullable=False)
    course_image=db.Column(db.String(50), nullable=False)



#initialising database
db.init_app(app)
app.app_context().push()


#creating database if not already exists
if os.path.exists("/SEEK.sqlite3")==False:
    db.create_all()

#___________________________validation____________________
def validate_username(a):
    if len(a)<4 or len(a)>20:
        return "length_error"
    if not a.isalnum():
        return "not_alphanumeric"
    return a
    
def validate_password(pwd):
    if len(pwd)<8 or len(pwd)>20:
        return "pwd_length"
    return pwd

def validate_email(mail):
    pattern = r'^[a-zA-Z0-9.]+@[a-zA-Z0-9]+\.[a-z]{2,}$'
    if re.match(pattern, mail):
        return True
    return False


#__________________________welcome page_____________________
@app.route('/', methods=["GET", "POST"])
def welcome():
    if request.method=="GET":
        return render_template("welcome.html")
    if request.method=="POST":
        login_type = request.form.get("login_type")
        if login_type=="admin":
            return redirect("/admin_login")
        if login_type=="user":
            return redirect("/user_login")


#--------------------------------------------ADMIN LOGIN------------------------------------
@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    if request.method=="GET":
        return render_template("admin_login.html")
    if request.method=="POST":
        usrname=request.form["ad_username"]
        passwrd=request.form["passwrd"]
        if validate_username(usrname)!=usrname:
            flash("Username length should be between 4 and 20 alphanumeric characters", "uname_error")
            return render_template("ad_login.html", usrname=usrname)
        adusrname=Admin.query.filter_by(ad_username=usrname).all()
        if len(adusrname)==0:
            flash("No Admin Exists with this Username! Enter correct credentials or Register as New Admin", "no_user")
            return redirect("/admin_login")
        if len(adusrname)>0:
            ad_uname=Admin.query.filter_by(ad_username=usrname).first()
            pwd=ad_uname.ad_pwd
            session["usr"]=usrname
            session["logged_in"]=True
            if pwd==passwrd:
                flash("Logged in successfully! Welcome to your dashboard", "success")
                return redirect("/admin")
            if validate_password(passwrd)!=passwrd:
                flash("Length of password should be at least 8 and at max 20 characters", "pwd_error")
                return render_template("admin_login.html", usrname=usrname)
            flash("Wrong password!", "error")
            return render_template("admin_login.html", usrname=usrname)

#------------------------ADMIN REGISTER----------------------------------------------------
@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():
    if request.method=="GET":
        return render_template("admin_register.html")
    if request.method=="POST":
        ad_fname=request.form["ad_fname"]
        ad_lname=request.form["ad_lname"]
        ad_email=request.form["email"]
        if not validate_email(ad_email):
            flash("Enter a valid email.","email_error")
            return render_template("admin_register.html", fname=ad_fname, lname=ad_lname)
        ad_uname=request.form["ad_username"]
        if validate_username(ad_uname)!=ad_uname:
            flash("Length of username should be between 4 and 20 alphanumeric characters", "uname_error")
            return render_template("admin_register.html", fname=ad_fname, lname=ad_lname, email=ad_email )
        ad_passwrd=request.form["ad_pwd"]
        if validate_password(ad_passwrd)!=ad_passwrd:
            flash("Length of password should be at least 8 and at max 20 characters", "pwd_error")
            return render_template("admin_register.html", fname=ad_fname, lname=ad_lname, uname=ad_uname, email=ad_email )      
        adusrname=Admin.query.filter_by(ad_username=ad_uname).all()
        if len(adusrname)!=0:
            flash("Username already exists! Try some other username.","usrname_exist")
            return render_template("admin_register.html", fname=ad_fname, lname=ad_lname, uname=ad_uname, email=ad_email )
        ad_data=Admin(ad_username=ad_uname, ad_fname=ad_fname,ad_lname=ad_lname,ad_email=ad_email,ad_pwd=ad_passwrd)
        db.session.add(ad_data)
        db.session.commit()
        flash("Registered as admin successfully", "success")
        return redirect("/admin_login")



#---------------------ADMIN LOGOUT---------------------------------------------------------
@app.route("/admin_logout", methods=["GET", "POST"])
def ad_logout():
    session.pop("usr", None)
    session["logged_in"]=False
    flash("Logged out successfully!", "success")
    return redirect("/")



#----------------USER LOGIN-----------------------------------------------------
@app.route('/user_login', methods=["GET", "POST"])
def user_login():
    if request.method=="GET":
        return render_template("user_login.html")
    if request.method=="POST":
        usrname=request.form["username"]
        passwrd=request.form["passwrd"]
        if validate_username(usrname)!=usrname:
            flash("Length of username should be between 4 and 20 alphanumeric characters", "uname_error")
            return render_template("user_login.html", usrname=usrname)
        usr=Users.query.filter_by(user_username=usrname).all()
        if len(usr)==0:
            flash("No User Exists with this Username! Enter correct credentials or Register as New User", "no_user")
            return redirect("/user_login")
        if len(usr)>0:
            user_uname=Users.query.filter_by(user_username=usrname).first()
            session["user"]=usrname
            session["user_logged_in"]=True
            pwd=user_uname.user_pwd
            if pwd==passwrd:
                flash("Logged in successfully! Welcome to your dashboard", "success")
                return redirect("/dashboard")
            if validate_password(passwrd)!=passwrd:
                flash("Length of password should be at least 8 and at max 20 characters", "pwd_error")
                return render_template("user_login.html", usrname=usrname)
            flash("Wrong password!", "error")
            return render_template("user_login.html", usrname=usrname)



#------------------------------------------------USER REGISTER----------------------------------------------------
@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method=="GET":
        return render_template("user_register.html")
    if request.method=="POST":
        u_fname=request.form["u_fname"]
        u_lname=request.form["u_lname"]
        u_email=request.form["u_email"]
        if not validate_email(u_email):
            flash("Enter a valid email.","email_error")
            return redirect("/user_register")
        u_uname=request.form["u_username"]
        if validate_username(u_uname)!=u_uname:
            flash("Length of username should be between 4 and 20 alphanumeric characters", "uname_error")
            return redirect("/user_register")
        u_passwrd=request.form["u_pwd"]
        if validate_password(u_passwrd)!=u_passwrd:
            flash("Length of password should be at least 8 and at max 20 characters", "pwd_error")
            return redirect("/user_register")
        uusrname=Users.query.filter_by(user_username=u_uname).all()
        if len(uusrname)!=0:
            flash("Username already exists! Try some other username.","usrname_exist")
            return redirect("/user_register")
        u_data=Users(user_username=u_uname, user_fname=u_fname,user_lname=u_lname,user_email=u_email ,user_pwd=u_passwrd)
        db.session.add(u_data)
        db.session.commit()
        flash("Registered as user successfully", "success")
        return redirect("/user_login")

#---------------------------USER LOGOUT-----------------------------------------------------
@app.route("/user_logout", methods=["GET", "POST"])
def user_logout():
    session.pop("user", None)
    session["user_logged_in"]=False
    flash("Logged out successfully!", "success")
    return redirect("/")







#------------------------------------------ADMIN DASHBOARD---------------------------------------------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method=="GET":
        if session["logged_in"]:
            usrname=session["usr"]
            adusr=Admin.query.filter_by(ad_username=usrname).first()
            ad_id=adusr.admin_id
            course_details=course.query.all()
            return render_template("admin_dashboard.html", admin_username=usrname, cat_det=course_details)
        else:
            return redirect("/admin_login")
    



#----------------------------------------------CREATE course-----------------------------------------------------
@app.route("/admin/create_course", methods=["GET", "POST"])
def create_course():
    if request.method == "GET":
        if session.get("logged_in"):
            usrname = session["usr"]
            return render_template("add_course.html", admin_username=usrname)
        return redirect("/admin_login")

    if request.method == "POST":
        cat_name = request.form["cat_name"]
        cat_details = request.form["cat_details"]
        usrname = session["usr"]
        cat_image = request.files["cat_img"]
        cat_creator = Admin.query.filter_by(ad_username=usrname).first()
        cat_creator_id = cat_creator.admin_id
        file_name = secure_filename(cat_image.filename)

        if file_name != "":
            file_ext = os.path.splitext(file_name)[1]
            unique_filename = str(uuid.uuid4()) + file_ext
            if file_ext not in app.config["UPLOAD_EXTENSIONS"]:
                abort(400)
            cat_image.save(os.path.join(app.config["UPLOAD_PATH"], unique_filename))

        course_data = course(
            course_name=cat_name,
            course_details=cat_details,
            course_image=unique_filename,
        )
        db.session.add(course_data)
        db.session.commit()
        flash("Course created successfully!", "success")
        return redirect("/admin")


#------------------------------------------------CREATE content INSIDE course------------------------------------------
@app.route("/admin/<cat_id>/create_content", methods=["GET", "POST"])
def create_content(cat_id):
    if request.method == "GET":
        if session.get("logged_in"):
            usrname = session["usr"]
            return render_template('add_content.html', admin_username=usrname, cat_id=cat_id)
        return redirect("/admin_login")

    if request.method == "POST":
        content_type = request.form.get("content_type")
        p_name = request.form["p_name"]

        if content_type == "assignment":
            question = request.form["assignment_question"]
            option_a = request.form["option_a"]
            option_b = request.form["option_b"]
            option_c = request.form["option_c"]
            option_d = request.form["option_d"]
            correct_answer = request.form["correct_answer"]

            assignment_data = MCQAssignment(
                question=question,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer,
                content_name=p_name,
                course_id=cat_id
            )

            db.session.add(assignment_data)
            db.session.commit()
            flash("Assignment created successfully!", "success")
            return redirect("/admin/" + cat_id + "/contents")

        elif content_type == "video":
            p_transcript = request.form["p_transcript"]
            p_link = request.form["p_link"]

            content_data = contents(
                content_name=p_name,
                content_transcript=p_transcript,
                content_course_id=cat_id,
                content_link=p_link
            )

            db.session.add(content_data)
            db.session.commit()
            flash("Content created successfully!", "success")
            return redirect("/admin/" + cat_id + "/contents")

        elif content_type == "programming":
            question = request.form["programming_question"]

            coding_data = Coding(
                coding_question=question,
                content_name=p_name
            )

            db.session.add(coding_data)
            db.session.commit()
            flash("Programming question created successfully!", "success")
            return redirect("/admin/" + cat_id + "/contents")

        elif content_type == "subjective":
            question = request.form["subjective_question"]

            subjective_data = Subjective(
                subjective_question=question,
                content_name=p_name
            )

            db.session.add(subjective_data)
            db.session.commit()
            flash("Subjective question created successfully!", "success")
            return redirect("/admin/" + cat_id + "/contents")


    # Handle other cases
    return redirect("/admin_login")



#------------------------------------------LISTING AVAILABLE contents FOR ADMIN-------------------------------------------------
@app.route("/admin/<cat_id>/contents", methods=["GET", "POST"])
def admin_content(cat_id):
    if request.method == "GET":
        if session.get("logged_in"):
            admin_username = session["usr"]
            content_list = contents.query.filter_by(content_course_id=cat_id).all()
            mcq_assignments = MCQAssignment.query.filter_by(course_id=cat_id).all()
            coding_questions = Coding.query.all()
            subjective_questions = Subjective.query.all()  # Fetch all subjective questions

            # Extracting selected content, MCQ, coding, and subjective question based on query parameters
            selected_content_id = request.args.get("selected")
            selected_mcq_id = request.args.get("selected_mcq")
            selected_coding_id = request.args.get("selected_coding")
            selected_subjective_id = request.args.get("selected_subjective")  # New line for subjective question

            selected_content = contents.query.get(selected_content_id) if selected_content_id else None
            selected_mcq = MCQAssignment.query.get(selected_mcq_id) if selected_mcq_id else None
            selected_coding = Coding.query.get(selected_coding_id) if selected_coding_id else None
            selected_subjective = Subjective.query.get(selected_subjective_id) if selected_subjective_id else None  # Fetch selected subjective question

            return render_template(
                "contents.html",
                admin_username=admin_username,
                cat_id=cat_id,
                content_list=content_list,
                selected_content=selected_content,
                mcq_assignments=mcq_assignments,
                mcq_selected_content=selected_mcq,
                coding_questions=coding_questions,
                selected_coding=selected_coding,
                subjective_questions=subjective_questions,  # Pass subjective questions to template
                selected_subjective=selected_subjective  # Pass selected subjective question to template
            )
        return redirect("/admin_login")





        
    


#-------------------------------------------UPDATING course---------------------------------------------------------
@app.route("/admin/<cat_id>/update", methods=["GET", "POST"])
def update_course(cat_id):
    if request.method=="GET":
        if session["logged_in"]:
            usrname=session["usr"]
            cat_details=course.query.filter_by(course_id=cat_id).first()
            return render_template("update_course.html", cat_details=cat_details, admin_username=usrname)
        return redirect("/admin_login")
    if request.method=="POST":
        cat_details=course.query.filter_by(course_id=cat_id).first()
        cat_name=request.form["cat_name"]
        cat_text=request.form["cat_text"]
        cat_image=request.files["cat_img"]
        cat_details.course_name=cat_name
        cat_details.course_details=cat_text
        file_name=secure_filename(cat_image.filename)
        if file_name!="":
            file_ext=os.path.splitext(file_name)[1]
            renamed_file_name=file_ext
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            cat_image.save(os.path.join(app.config['UPLOAD_PATH'], renamed_file_name))
        cat_details.course_image=renamed_file_name 
        db.session.commit()
        flash("categroy details updated successfully!", "success")
        return redirect("/admin")



#--------------------------------------DELETING course----------------------------------------------------------
@app.route("/admin/<cat_id>/delete", methods=["GET", "POST"])
def delete_cat(cat_id):
    if session["logged_in"]:
        usrname=session["usr"]
        return render_template("delete_course.html", admin_username=usrname, cat_id=cat_id)
    return redirect("/admin_login")



#------------------------------------COMFIRMED DELETING CATEGORY-------------------------------------------------
@app.route("/admin/<cat_id>/delete_course", methods=["GET", "POST"])
def delete_course(cat_id):
    categry = course.query.filter_by(course_id=cat_id).first()
    content=contents.query.filter_by(content_course_id=categry.course_id).all()
    if request.method=="GET":
        if session["logged_in"]:
            db.session.delete(categry)
            for content in content:
                db.session.delete(content)
            db.session.commit()
        flash("Venue deleted successfully!","success")
        return redirect("/admin")
    return redirect("/admin_login")




#----------------------------------------------UPDATING CONTENTS--------------------------------------------
@app.route("/admin/<cat_id>/<content_id>/update", methods=["GET", "POST"])
def update_show(cat_id, content_id):
    if request.method == "GET":
        if session.get("logged_in"):
            usrname = session["usr"]
            content_detail = contents.query.filter_by(content_id=content_id).first()
            mcq_selected_content = MCQAssignment.query.filter_by(id=content_id).first()
            coding_selected_content = Coding.query.filter_by(question_id=content_id).first()
            subjective_selected_content = Subjective.query.filter_by(question_id=content_id).first()  # Fetch subjective question details
            return render_template(
                "update_content.html", 
                content_detail=content_detail, 
                admin_username=usrname, 
                cat_id=cat_id, 
                mcq_selected_content=mcq_selected_content, 
                coding_selected_content=coding_selected_content,
                subjective_selected_content=subjective_selected_content
            )
        return redirect("/admin_login")
    
    if request.method == "POST":
        # Process form submission
        content_detail = contents.query.filter_by(content_id=content_id).first()
        content_name = request.form["p_name"]
        content_detail.content_name = content_name
        content_detail.content_type = request.form["content_type"]

        if content_detail.content_type == "video":
            content_detail.content_link = request.form["p_link"]
            content_detail.content_transcript = request.form["p_transcript"]
        elif content_detail.content_type == "assignment":
            content_detail.assignment_question = request.form["assignment_question"]
            content_detail.option_a = request.form["option_a"]
            content_detail.option_b = request.form["option_b"]
            content_detail.option_c = request.form["option_c"]
            content_detail.option_d = request.form["option_d"]
            content_detail.correct_answer = request.form["correct_answer"]
        elif content_detail.content_type == "programming":
            content_detail.programming_question = request.form["programming_question"]
            content_detail.name = request.form["Name"]
        elif content_detail.content_type == "subjective":  # Handle subjective questions
            subjective_selected_content = Subjective.query.filter_by(question_id=content_id).first()
            if subjective_selected_content:
                subjective_selected_content.subjective_question = request.form["subjective_question"]
            else:
                new_subjective_question = Subjective(
                    question_id=content_id,
                    subjective_question=request.form["subjective_question"],
                    content_name=content_name
                )
                db.session.add(new_subjective_question)

        db.session.commit()
        flash("Content details updated successfully!", "success")
        return redirect(f"/admin/{cat_id}/contents")



    

#------------------------------------------------DELETING -------------------------------------------------
@app.route("/admin/<cat_id>/<content_id>/delete", methods=["GET", "POST"])
def delete_content(cat_id, content_id):
    if session["logged_in"]:
        content = contents.query.filter_by(content_id=content_id).first()
        
        if content:
            db.session.delete(content)
            db.session.commit()
            flash("Content deleted successfully!", "success")
            return redirect("/admin/" + cat_id + "/contents")
        
        flash("Content not found!", "error")
        return redirect("/admin/" + cat_id + "/contents")
    
    return redirect("/admin_login")



@app.route("/admin/<cat_id>/<id>/delete_mcq", methods=["GET", "POST"])
def delete_mcq(cat_id, id):
    if session["logged_in"]:
        content = MCQAssignment.query.filter_by(id=id).first()
        
        if content:
            db.session.delete(content)
            db.session.commit()
            flash("Content deleted successfully!", "success")
            return redirect("/admin/" + cat_id + "/contents")
        
        flash("Content not found!", "error")
        return redirect("/admin/" + cat_id + "/contents")
    
    return redirect("/admin_login")

@app.route("/admin/<cat_id>/<question_id>/delete_coding", methods=["GET", "POST"])
def delete_coding_problem(cat_id,question_id):
    if session["logged_in"]:
        content = Coding.query.filter_by(question_id=question_id).first()
        
        if content:
            db.session.delete(content)
            db.session.commit()
            flash("Content deleted successfully!", "success")
            return redirect("/admin/" + cat_id + "/contents")
        
        flash("Content not found!", "error")
        return redirect("/admin/" + cat_id + "/contents")
    
    return redirect("/admin_login")

@app.route("/admin/<cat_id>/<question_id>/delete_subjective", methods=["GET", "POST"])
def delete_subjective(cat_id, question_id):
    if session.get("logged_in"):
        content = Subjective.query.filter_by(question_id=question_id).first()
        
        if content:
            db.session.delete(content)
            db.session.commit()
            flash("Content deleted successfully!", "success")
            return redirect(f"/admin/{cat_id}/contents")
        
        flash("Content not found!", "error")
        return redirect(f"/admin/{cat_id}/contents")
    
    return redirect("/admin_login")


#---------------------------------------------ADMIN PROFILE-----------------------------------------------------
@app.route("/a_profile", methods=["GET", "POST"])
def a_profile():
    if session["logged_in"]:
        usrname=session["usr"]
        admin_prof=Admin.query.filter_by(ad_username=usrname).first()
        return render_template("admin_profile.html", admin_det=admin_prof)
    return redirect("/admin_login")




#---------------------------------------------USER DASHBOARD---------------------------------------------------

@app.route("/dashboard", methods=["GET", "POST"])
def user_dashboard():
    if request.method == "GET":
        if session.get("user_logged_in"):
            username = session["user"]
            user = Users.query.filter_by(user_username=username).first()
            courses = course.query.all()
            
            return render_template("user_dashboard.html", usr_usrname=user.user_username, courses=courses)
        return redirect("/user_login")
#____________________________________USER CONTENTS__________________________________
@app.route("/dashboard/course/<course_id>", methods=["GET"])
def course_page(course_id):
    if session.get("user_logged_in"):
        username = session["user"]
        user = Users.query.filter_by(user_username=username).first()
        course_data = course.query.get(course_id)  # Ensure 'Course' matches your model name
        content = contents.query.filter_by(content_course_id=course_id).all()  # Ensure 'Contents' matches your model name
        mcq_assignments = MCQAssignment.query.filter_by(course_id=course_id).all()
        coding_questions = Coding.query.all()
        subjective_questions = Subjective.query.all()

        selected_content_id = request.args.get("selected")
        selected_mcq_id = request.args.get("selected_mcq")
        selected_coding_id = request.args.get("selected_coding")
        selected_subjective_id = request.args.get("selected_subjective")

        selected_content = contents.query.get(selected_content_id) if selected_content_id else None
        selected_mcq = MCQAssignment.query.get(selected_mcq_id) if selected_mcq_id else None
        selected_coding = Coding.query.get(selected_coding_id) if selected_coding_id else None
        selected_subjective = Subjective.query.get(selected_subjective_id) if selected_subjective_id else None

        return render_template(
            "user_content.html",
            usr_usrname=user.user_username,
            course_name=course_data.course_name,
            content=content,
            selected_content=selected_content,
            mcq_assignments=mcq_assignments,
            selected_mcq=selected_mcq,
            coding_questions=coding_questions,
            selected_coding=selected_coding,
            subjective_questions=subjective_questions,  # Pass the list of subjective questions to the template
            selected_subjective=selected_subjective
        )
    return redirect("/user_login")



#--------------------------delete item------------------------------------        
@app.route("/dashboard/delete_prompt_item/<int:prompt_id>", methods=["POST"])
def delete_prompt_item(prompt_id):
    prompt = prompts.query.get_or_404(prompt_id)
    db.session.delete(prompt)
    db.session.commit()
    flash("prompt item deleted successfully.", "success")
    return redirect("/dashboard")

#--------------------------------------------------USER PROFILE--------------------------------------------------
@app.route("/user_profile", methods=["GET", "POST"])
def user_profile():
    if session["user_logged_in"]:
        usrname=session["user"]
        user_prof=Users.query.filter_by(user_username=usrname).first()
        return render_template("user_profile.html", user_det=user_prof)
    return redirect("/user_login")

#----------------------------------------prompt-------------------------------------------------------------    
@app.route('/prompt', methods=['GET'])
def prompt():
    return render_template('prompt.html')

@app.route('/process_web_prompt', methods=['POST'])
def process_web_prompt():
    try:
        prompt = request.form.get('prompt')
        print(f"Received prompt: {prompt}\n The user wants answer without context")

        # Generate response using model
        response = ollama.chat(model='gemma:2b', messages=[
            {'role': 'user', 'content': prompt}
        ])
        answer = response['message']['content']
        print(f"Generated answer: {answer}")

        # Return the generated response
        return jsonify({'Answer': answer}), 200
    except KeyError as e:
        return jsonify({'error': f"Missing form data: {e.args[0]}"}), 400
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500


@app.route('/process_prompt', methods=['POST'])
def process_prompt():
    if session.get("user_logged_in"):
        username = session["user"]
        user = Users.query.filter_by(user_username=username).first()

        if request.method == 'POST':
            # Get the prompt from the form data
            prompt = request.form.get('prompt')
            print(f"Received prompt: {prompt}\n The user wants answer in context of video")  # Debugging statement
            
            # Get the content ID from the form data
            content_id = request.form.get('content_id')
            print(f"Received content_id: {content_id}")  # Debugging statement
            
            # Retrieve the content object using the content ID
            content = db.session.query(contents).get(content_id)
            
            if content:
                # Extract the transcript from the content
                transcript = content.content_transcript
                #print(f"Extracted transcript: {transcript}")  # Debugging statement

                # Generate response using model
                response = ollama.chat(model='gemma:2b', messages=[
                    {'role': 'system', 'content': transcript},
                    {'role': 'user', 'content': prompt}
                ])
                answer = response['message']['content']
                print(f"Generated answer: {answer}")  # Debugging statement

                # Save the new prompt to the database
                new_prompt = prompts(pprompt=prompt, ptranscript=transcript, pcontent_id=content_id, puser_id=user.user_id)
                db.session.add(new_prompt)
                db.session.commit()
                
                # Return the generated response
                return jsonify({'Answer': answer}), 200
            else:
                return jsonify({'error': 'Content not found.'}), 404
    else:
        return jsonify({'error': 'User not logged in.'}), 401


def process_coding_question(coding_question):
    response = ollama.chat(model='gemma:2b', messages=[
        {
            'role':'user',
            'content': coding_question,
        },
    ])
    answer = response['message']['content']
    print(f"ANSWER=\n{answer}")
    # Remove ```python and ``` from the answer
    answer = answer.replace('```python', '').replace('```', '').replace('**', '')
    return answer

def process_coding_hint(coding_question, additional_input):
    response = ollama.chat(model='gemma:2b', messages=[
        {
            'role':'user',
            'content': coding_question,
        },
        {
            'role':'user',
            'content': " Give hint to solve the question, based on the question, dont provide the exact code,but provide insightss whats can be done for the question, steps ,functions, variables to make and whatever necessary ,the code writen by the user till now is : "+ additional_input,
        }
    ])
    answer = response['message']['content']
    print(f"ANSWER=\n{answer}")
    answer = answer.replace('```python', '').replace('```', '').replace('**', '')
    return answer


# GET EXACT ANSWER TO THE CODING QUESTION
@app.route('/get_coding_answer', methods=['POST'])
def get_coding_answer():
    try:
        print("USER WANTS THE EXACT ANSWER")
        data = request.get_json()
        coding_question = data['coding_question']
        print(f"Recieved Coding question = {coding_question}")
        answer = process_coding_question(coding_question)
        
        return jsonify({'answer': answer}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET HINT TO THE CODING QUESTION
@app.route('/get_coding_hint', methods=['POST'])
def get_coding_hint():
    try:
        print("INSIDE TRY BLOCK")
        data = request.get_json()
        coding_question = data['coding_question']
        additional_input = data['additional_input']
        print(f"Received DATA: Question = {coding_question}, Additional Input = {additional_input}")
        
        # Process the coding question and additional input to generate a hint
        hint = process_coding_hint(coding_question, additional_input)
        
        return jsonify({'hint': hint}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500



from flask import Flask, request, jsonify
import io
import contextlib
import logging


def run_code(user_code, test_input, expected_output):
    """
    Executes the user code and tests it against the given input and expected output.
    """
    # Create a new local namespace for the code execution
    local_namespace = {}
    
    # Define a function to capture the output
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            # Execute the user's code
            exec(user_code, {}, local_namespace)
            
            # Retrieve the function name
            function_name = next(iter(local_namespace.keys()))
            
            # Call the user's function with the test input
            result = local_namespace[function_name](*test_input)
            
            # Check if the result matches the expected output
            if result == expected_output:
                return True, "Test passed!"
            else:
                return False, f"Test failed! Expected {expected_output}, but got {result}."
        except Exception as e:
            return False, f"Error executing code: {str(e)}"

@app.route('/check_code', methods=['POST'])
def check_code():
    """
    Endpoint to receive user code, test input, and expected output,
    and check if the code produces the correct result.
    """
    try:
        data = request.get_json()
        user_code = data['code']
        test_input = data['input']
        expected_output = data['expected_output']
        
        # Check the user code
        is_correct, message = run_code(user_code, test_input, expected_output)
        
        return jsonify({
            'is_correct': is_correct,
            'message': message
        }), 200
    except Exception as e:
        return jsonify({
            'is_correct': False,
            'message': str(e)
        }), 500


def process_feedback(question, answer, feedback_type):
    try:
        if feedback_type == 'cohesiveness':
            prompt = f"This was the question: {question} Now we have to give feedback to the student about the cohesiveness of the answer. Does the answer have a proper flow or not? Is the answer relevant to the question? If not, give him proper feedback about these points. Your feedback should not exceed 100 words. Your feedback should be in form of bullet points. Include a '\n' after every bullet point. This is the answer written by student: {answer}"
        elif feedback_type == 'grammar':
            prompt = f'An assignment has this question: "{question}" This is the answer written by student: {answer} Knowing the the question and answer, list any grammatical mistakes that the answer may have. Also explain how those mistakes can be rectified, keep the response short. Write the answer in bullet points. Include a "\n" after every bullet point.'
        else:
            prompt = f'An assignment has this question: "{question}" This is the answer written by student: {answer} Knowing the question and the answer, give me a percentage score which tells how much the content is AI generated. Give your answer in the following format: "The given content seems to be <percentage>% AI generated."'

        response = ollama.chat(model='gemma:2b', messages=[
            {'role': 'user', 'content': prompt}
        ])
        feedback = response['message']['content']
        feedback = feedback.replace('```python', '').replace('```', '').replace('**', '')
        print(f"Answer by OLLAMA for {feedback_type} is:\n{feedback}")
        return feedback
    except Exception as e:
        feedback = f"The answer could not be processed because of technical issue {e}"
        return feedback

@app.route("/evaluate_subjective", methods=["POST"])
def evaluate_subjective():
    if session.get("user_logged_in"):
        try:
            data = request.get_json()
            question = data.get("question")
            answer = data.get("answer")

            cohesiveness_feedback = process_feedback(question, answer, 'cohesiveness')
            grammar_feedback = process_feedback(question, answer, 'grammar')
            plagisrism_feedback = process_feedback(question, answer, 'plagiarism')

            if cohesiveness_feedback is None or grammar_feedback is None:
                raise ValueError("Feedback processing failed.")
            
            response = {
                'cohesiveness_feedback': cohesiveness_feedback,
                'grammar_feedback': grammar_feedback,
                'plagisrism_feedback': plagisrism_feedback
            }
            return jsonify({'response': response}), 200

        except Exception as e:
            logging.error(f"Error in evaluate_subjective: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        return redirect("/user_login")

@app.route("/dashboard/course/1/GA1", methods=["GET","POST"])
def show_GA1():
    if request.method=="POST":
        pass
    return render_template("GA_1.html")

@app.route("/evaluate_GA", methods=["POST"])
def evaluate_GA():
    if request.method=='POST':
        data = request.get_json()
        # print(f"DATA=\n\n***********\n")
        assert isinstance(data, dict),  "WARNING! DATA SHOULD be A DICT"

        prompt = '''An assignment was given to a student. The topics for the assignment are: Logarithms and Quadratic equations. Here I am giving you the questions that were given in the assignment, the answer that was marked by the student, and the actual answer of that question. You have to analyse the information and suggest the learning path for that student. The feedback should include: 
        1. In which topics he needs to focus more? 
        2. In which topic he is strong?
        3. Suggest atleast 2 questions based on the topic in which the student seems weak.

        Here is the required information:
        {'''

        for (k,v) in data.items():
            text = f'''
Question asked: {k}
Answer given by student: {v[0]} 
Actual answer: {v[1]}, \n\n'''
            prompt+=text
        prompt+="}"
        text = '''Your answer should be in the following format:
        The topics in which the student seems weak is/are: <relevant info here>.
        The topics in which the student seems strong is/are: <relevant info here>.
        Here are some additional questions for student to practice: <numerical questions here>'''
        prompt+=text
        # print("GENERATED PROMPT = \n*********\n",prompt)
        # return jsonify({'Answer': "hello \n world**#"})
        try:
            # Generate response using model
            response = ollama.chat(model='gemma:2b', messages=[
                {'role': 'user', 'content': prompt}
            ])
            answer = response['message']['content']
            print(f"Generated answer: {answer}")

            # Return the generated response
            return jsonify({'Answer': answer}), 200
        except KeyError as e:
            return jsonify({'error': f"Missing form data: {e.args[0]}"}), 400
        except Exception as e:
            return jsonify({'error': f"An error occurred: {str(e)}"}), 500

#----------------------------course DETAILS-------------------------------------------------
@app.route("/course_details/<cat_id>", methods=["GET"])
def content_course(cat_id):
    if request.method=="GET":
        if session["user_logged_in"]:
            course_det=course.query.filter_by(course_id=cat_id).first()
            content_det=contents.query.filter_by(content_course_id=course_det.course_id).all()
            return render_template("course_details.html", course=course_det, contents=content_det)
        return redirect("/")

#-----------------------content DETAILS---------------------------------
@app.route("/content/<content_id>", methods=["GET"])
def content_details(content_id):
    if request.method=="GET":
        if session["user_logged_in"]:
            content_det=contents.query.filter_by(content_id=content_id).first()
            return render_template("content_details.html", content=content_det)
        return redirect("/")
     
#Running the app
if __name__=="__main__":
    app.debug=True
    app.run()                


