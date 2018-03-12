###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
import requests
import json

## App setup code
app = Flask(__name__)
app.debug = True
app.use_reloader = True

## All app.config values
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)
manager = Manager(app)

migrate = Migrate(app, db) # For database use/updating
manager.add_command('db', MigrateCommand) # Add migrate command to manager
######################################
######## HELPER FXNS (If any) ########
######################################




##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

## - Video
## -- id (Integer, ID of name -- ForeignKey)
## -- Title (String, up to 250 charc)
class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250))
    name_id = db.Column(db.Integer, db.ForeignKey('names.id'))

    def __repr__(self):
        return self.title

## - Subscriber
## -- id (Integer, Primary Key)
## -- username (String, up to 64 chars, Unique=True, has to be one word  )
## -- age (integer)
class Subscriber(db.Model):
    __tablename__='subscribers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    age = db.Column(db.Integer)
    channels = db.relationship('Channel',backref='Subscriber')

    def __repr__(self):
        return "Username: {} | Age: {}".format(self.username, self.age)



## - Channel
## -- id (Integer, ID of subscriber -- ForeignKey)
## -- Name (String, up to 250 charac)
## -- Rating (Integer only 1 to 5)
## -- Subscriber (YES/NO)

class Channel(db.Model):
    __tablename__='channels'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    rating = db.Column(db.Integer)
    subscriber = db.Column(db.String(3))
    subscriberID = db.Column(db.Integer, db.ForeignKey('subscribers.id'))



    def __repr__(self):
        if self.subscriber == 'yes':
            return " favorite channel is {}. The user rated this channel {} out of 5. The user is subscribed to this channel.".format(self.name, self.rating)
        elif self.subscriber == 'no':
            return " favorite channel is {}. The user rated this channel {} out of 5. The user is NOT subscribed to this channel.".format(self.name, self.rating)
        else:
            return "not everything is filled out correctly"



###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name.",validators=[Required()])
    submit = SubmitField()

## Video Form
## video: what term do you want to look up on youtube (Required, string)

class VideoForm(FlaskForm):
    title = StringField("Search for a YouTube video.", validators=[Required()])
    submit = SubmitField('Search')

## Channel Form
## username: username of subscriber (required, no more than 64 charac, has to be one word)
## age: user's age (Required, string value, can only be numbers between 5-100)
## channel: name of the channel (Required, String value)
## Rating: On the scale of 1-5 much do you like this channel? (1-5) or integer input?
## Subscriber: YES or NO (RadioField)


class ChannelForm(FlaskForm):
    username = StringField("Enter your username.", validators=[Required()])
    age = StringField("Enter your age. ", validators=[Required()])
    channel = StringField("What is the name of your favorite YouTube channel? ", validators=[Required()])
    rating = StringField("How would you rate this channel out of 5?", validators=[Required()])
    subscriber = StringField('Are you subsribed to this channel on Youtube? (Must answer with "yes" or "no")', validators=[Required()])
    submit = SubmitField('Submit')

    def validate_subscriber(self, field):
        if field.data not in ['yes','no']:
            raise ValidationError("Please enter 'yes' or 'no.'")

    def validate_rating(self, field):
        if field.data not in ["1","2","3","4","5"]:
            raise ValidationError("Rating must be from 1-5")


#######################
###### VIEW FXNS ######
#######################

@app.route('/', methods=['GET', 'POST'])
def home():
    form = NameForm()
 # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name=name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('base.html', form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)


######################

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


#####################
## Channel Form
## username: username of subscriber (required, no more than 64 charac, has to be one word)
## age: user's age (Required, string value, can only be numbers between 5-100)
## channel: name of the channel (Required, String value)
## Rating: On the scale of 1-5 much do you like this channel? (1-5) or integer input?
## Subscriber: YES or NO (RadioField)

@app.route('/channels', methods = ['GET','POST'])
def channel_info():
    cform = ChannelForm()
    num_submissions = len(Channel.query.all())
    if cform.validate_on_submit():
        username = cform.username.data
        age = cform.age.data
        channel = cform.channel.data
        rating = cform.rating.data
        subscriber = cform.subscriber.data

        s = Subscriber.query.filter_by(username=username).first()
        if not s:

            s = Subscriber(username = username, age = age)
            db.session.add(s)
            db.session.commit()

        else:
            sub_id = s.id
            c = Channel.query.filter_by(name = channel, subscriberID = sub_id).first()
            if c:
                flash ("This channel has already been submitted.")
                return redirect(url_for('all_channels'))
            else:
                c = Channel(name = channel, rating = rating, subscriber = subscriber, subscriberID = sub_id)
                db.session.add(c)
                db.session.commit()
                return redirect(url_for('all_channels'))


    #CODE DIRECTLY FROM HW3 (210-212)
    errors = [v for v in cform.errors.values()]
    if len(errors) >0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))

    return render_template('channelform.html', form=cform, num_submissions=num_submissions)





@app.route('/channelresults')
def all_channels():
    channels = Channel.query.all()
    all_subscribers = Subscriber.query.all()
    cs = []
    for c in channels:
        subscribers = Subscriber.query.filter_by(id=c.subscriberID).all()
        tup = (c, subscribers[0].username)
        cs.append(tup)
    return render_template('channel_info.html',channels=cs,subscribers=all_subscribers)


@app.route('/videos', methods=['GET','POST'])
def video_info():
    vform = VideoForm()
    return render_template('videoform.html', form=vform)

@app.route('/videoresults')
def all_videos():
    title = request.args["title"]
    t = Video(title = title)
    db.session.add(t)
    db.session.commit()

    videos = Video.query.all()
    recent = videos[-1]
    baseurl = 'https://www.googleapis.com/youtube/v3/search/'
    param = {'q':str(recent), 'part':'snippet', 'maxResults':10, 'type':'', 'key':'AIzaSyCkd930n_MCJrOsWJJPSoLk22lb0c4C-94'}
    response = requests.get(baseurl, params = param)
    response_dict = json.loads(response.text)
    objects = response_dict['items']

    new = []
    for item in objects:
        if item['id']['kind'] == 'youtube#video':
            new.append(item)

    return render_template('video_info.html', videos = videos, objects = new)

@app.route('/search_history')
def history():
    videos = Video.query.all()
    return render_template('videosearches.html',videos=videos)
## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
if __name__ == '__main__':
    db.create_all()
    app.run(use_reloader=True,debug=True)
