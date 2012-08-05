import cgi
import os
import datetime
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms

# Models and forms
class Auction(db.Model):
    auction_date = db.DateTimeProperty(required=True)
    auction_rain_date = db.DateTimeProperty()
    title = db.StringProperty(required=True)
    preface = db.StringProperty(multiline=True)
    postscript = db.StringProperty(multiline=True)
    owner = db.StringProperty()
    address = db.PostalAddressProperty()
    latlon = db.GeoPtProperty()
    driving_directions = db.TextProperty()

    def sections(self):
        sections = Section.all()
        sections.filter('auction = ', self)
        sections.order('order')
        return sections

    def images(self):
        images = Image.all()
        images.filter('auction = ', self)
        return images

    def __unicode__(self):
        return str(self.auction_date)

class AuctionForm(djangoforms.ModelForm):
    class Meta:
        model = Auction

class Section(db.Model):
    auction = db.ReferenceProperty(Auction)
    title = db.StringProperty()
    items = db.TextProperty()
    order = db.IntegerProperty()
    auction_split_wording = db.StringProperty()

class SectionForm(djangoforms.ModelForm):
    class Meta:
        model = Section

class Image(db.Model):
    auction = db.ReferenceProperty(Auction)
    image = db.BlobProperty()
    thumb = db.BlobProperty()
    caption = db.StringProperty()
    item_to_tag = db.StringProperty()

class ImageForm(djangoforms.ModelForm):
    class Meta:
        model = Image

# Pages
class MainPage(webapp.RequestHandler):
    def get(self):        
        auctions = Auction.all()
        auctions.filter('auction_date >=', datetime.datetime.today()-datetime.timedelta(days=1))
        self.response.out.write(template.render(fetch_template('main.html'), {'auctions': auctions}))

class AuctionPage(webapp.RequestHandler):
    def get(self, auction_key):
        auction_date = datetime.datetime.strptime(auction_key, '%m_%d_%Y_%H_%M')
        auctions = Auction.all()
        auctions.filter('auction_date =', auction_date)
        auction = auctions[0]
        self.response.out.write(template.render(fetch_template('auction.html'), {'auction': auction}))

class AdminPage(webapp.RequestHandler):
    def get(self):
        auctions = Auction.all()
        self.response.out.write(template.render(fetch_template('admin_main.html'), {'auctions': auctions}))

class AdminAuctionAddPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render(fetch_template('form_page.html'), {'form': AuctionForm()}))

    def post(self):
        form = AuctionForm(data=self.request.POST)
        if form.is_valid():
            # Save the data, and redirect to the view page
            entity = form.save(commit=False)
            entity.put()
            self.redirect('/admin/main')
        else:
            # Reprint the form
            self.response.out.write(template.render(fetch_template('form_page.html'), {'form': form}))

class AdminAuctionEditPage(webapp.RequestHandler):
    def get(self, id):
        id = int(id)
        auction = Auction.get(db.Key.from_path('Auction', id))
        form = AuctionForm(instance=auction)
        self.response.out.write(template.render(fetch_template('form_page.html'), {'form': form}))

    def post(self, id):
        id = int(id)
        auction = Auction.get(db.Key.from_path('Auction', id))
        form = AuctionForm(data=self.request.POST, instance=auction)
        if form.is_valid():
            # Save the data, and redirect to the view page
            entity = form.save(commit=False)
            entity.put()
            self.redirect('/admin/main')
        else:
            # Reprint the form
            self.response.out.write(template.render(fetch_template('form_page.html'), {'form': form}))

class AdminAuctionDeletePage(webapp.RequestHandler):
    def get(self, id):
        self.response.out.write(template.render(fetch_template('delete_page.html'),{}))

    def post(self, id):
        id = int(id)
        auction = Auction.get(db.Key.from_path('Auction', id))
        auction.delete()
        self.redirect('/admin/main')

class AdminSectionAddPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render(fetch_template('form_page.html'), {'form': SectionForm()}))

    def post(self):
        form = SectionForm(data=self.request.POST)
        if form.is_valid():
            # Save the data, and redirect to the view page
            entity = form.save(commit=False)
            entity.put()
            self.redirect('/admin/main')
        else:
            # Reprint the form
            self.response.out.write(template.render(fetch_template('form_page.html'), {'form': form}))

class AdminSectionEditPage(webapp.RequestHandler):
    def get(self, id):
        section = Section.get(id)
        form = SectionForm(instance=section)
        self.response.out.write(template.render(fetch_template('form_page.html'), {'form': form}))

    def post(self, id):
        section = Section.get(id)
        form = SectionForm(data=self.request.POST, instance=section)
        if form.is_valid():
            # Save the data, and redirect to the view page
            entity = form.save(commit=False)
            entity.put()
            self.redirect('/admin/main')
        else:
            # Reprint the form
            self.response.out.write(template.render(fetch_template('form_page.html'), {'form': form}))

class AdminSectionDeletePage(webapp.RequestHandler):
    def get(self, id):
        self.response.out.write(template.render(fetch_template('delete_page.html'),{}))

    def post(self, id):
        section = Section.get(id)
        section.delete()
        self.redirect('/admin/main')

class AdminImageAddPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render(fetch_template('image_form.html'), {'form': ImageForm()}))

    def post(self):
#        form = ImageForm(data=self.request.POST)
#        if form.is_valid():
            # Save the data, and redirect to the view page
#            entity = form.save(commit=False)
#            entity.put()
#            self.redirect('/admin/main')
        image = Image()
        image.auction = Auction.get(self.request.POST['auction'])
        image.caption = self.request.POST['caption']
        image.item_to_tag = self.request.POST['item_to_tag']
        img = self.request.get('image')
        image.image = db.Blob(img)
        image.image = images.resize(image.image, 800, 600)        
        image.thumb = images.resize(image.image, 200, 200)
        image.put()
        self.redirect('/admin/main')
#        else:
#            # Reprint the form
#            self.response.out.write(template.render(fetch_template('form_page.html'), {'form': form}))

class AdminImageEditPage(webapp.RequestHandler):
    def get(self, id):
        image = Image.get(id)
        form = ImageForm(instance=image)
        self.response.out.write(template.render(fetch_template('image_form.html'), {'form': form}))

    def post(self, id):
        image = Image.get(id)
        image.auction = Auction.get(self.request.POST['auction'])
        image.caption = self.request.POST['caption']
        image.item_to_tag = self.request.POST['item_to_tag']
        if(self.request.get('image')):
            img = self.request.get('image')
            image.image = db.Blob(img)
            image.thumb = images.resize(image.image, 200, 200)
        image.put()
        self.redirect('/admin/main')   

class AdminImageDeletePage(webapp.RequestHandler):
    def get(self, id):
        self.response.out.write(template.render(fetch_template('delete_page.html'),{}))

    def post(self, id):
        image = Image.get(id)
        image.delete()
        self.redirect('/admin/main')

class ServeImage (webapp.RequestHandler):
    def get(self, img_id):
      image = db.get(img_id)
      if image.image:
          self.response.headers['Content-Type'] = "image/jpg"
          self.response.out.write(image.image)
      else:
          self.error(404)

class ServeThumb (webapp.RequestHandler):
    def get(self, img_id):
      image = db.get(img_id)
      if image.thumb:
          self.response.headers['Content-Type'] = "image/jpg"
          self.response.out.write(image.thumb)
      else:
          self.error(404)

def fetch_template(name):
    path = os.path.join(os.path.dirname(__file__), 'templates', name)
    return path

def main():
    application = webapp.WSGIApplication(
                                         [('/admin/main', AdminPage),
                                          ('/admin/auction/add', AdminAuctionAddPage),
                                          (r'/admin/auction/edit/(.*)', AdminAuctionEditPage),
                                          (r'/admin/auction/delete/(.*)', AdminAuctionDeletePage),
                                          ('/admin/section/add', AdminSectionAddPage),
                                          (r'/admin/section/edit/(.*)', AdminSectionEditPage),
                                          (r'/admin/section/delete/(.*)', AdminSectionDeletePage),
                                          ('/admin/image/add', AdminImageAddPage),
                                          (r'/admin/image/edit/(.*)', AdminImageEditPage),
                                          (r'/admin/image/delete/(.*)', AdminImageDeletePage),                                          
                                          (r'/auction/(.*)', AuctionPage),
                                          (r'/image/(.*)', ServeImage),
                                          (r'/thumb/(.*)', ServeThumb),                                          
                                          ('/', MainPage),
                                          ],
                                         debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()