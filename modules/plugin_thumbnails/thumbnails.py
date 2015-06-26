"""
thumbnails.py

This file is part of the web2py plugin_thumbnails. 
It allows automatic creation of thumbnails from image upload fields.
Author: Carlos Cesar Caballero Diaz
License: LGPL

Usage:
db = DAL()
db.define_table('mytable',Field('myfield','string'),
                          Field('img','upload'))
from plugin_thumbnails.thumbnails import thumbnails     # imports thumbnails plugin
thumb = thumbnails(db)                                  # instantiate plugin and crete needed table
thumb.create(db.mytable.img)                            # create thumbnails for mytable img field
db.mytable.insert(myfield='Char',img=image)             # automatically create thumbnail for img field
db(db.mytable.id).img_thumbnail                         # get img thumbnail
db(db.mytable.id).update(img=new_image)                 # automatically update thumbnail
db(db.mytable.id).delete()                              # automatically delete thumbnail


Options:
thumb = thumbnails(db, autodelete=True)                 # enable autodelete of thumbnails images
thumb.create(db.mytable.img, (50,50))                   # thumbnails size of 50 x 50 px
"""

from gluon import *
import os

class thumbnails():

    def __init__(self, db, autodelete=False):
        self.db = db
        self._init_plugin_thumbnails_db(autodelete)

    def create(self, table_field, size=(175, 175), use_imageops=False):
        self.db[table_field._tablename]._after_insert.append(
            lambda fields,id: self._after_insert(table_field, fields, id, size, use_imageops))
        self.db[table_field._tablename]._after_update.append(
            lambda queryset,fields: self._after_update(table_field, fields, queryset, size, use_imageops))
        self.db[table_field._tablename]._before_delete.append(
            lambda queryset: self._before_delete(table_field, queryset))
        self.db[table_field._tablename][table_field.name+'_thumbnail'] = Field.Virtual(
            lambda row: self._get_thumbnail(table_field, row))
        
    def _init_plugin_thumbnails_db(self, autodelete):
        """
        Declare plugin table
        :param autodelete: if true remove images from hdd when delete fields
        """
        self.db.define_table('plugin_thumbnails',
                        Field('row_id','integer'),
                        Field('table_name'),
                        Field('field_name'),
                        Field('image_thumbnail','upload', autodelete=autodelete))

    def _after_insert(self, table_field, fields, id, size, use_imageops):
        self.make_thumbnail(table_field, id, size, use_imageops)
        return False

    def _after_update(self, table_field, fields, queryset, size, use_imageops):
        query = queryset.select(self.db[table_field._tablename].id).first()
        self.make_thumbnail(table_field, query.id, size, use_imageops)
        return False

    def _before_delete(self, table_field, queryset):
        query = queryset.select(self.db[table_field._tablename].id).first()
        self.db((self.db.plugin_thumbnails.row_id == query.id) & (self.db.plugin_thumbnails.table_name == table_field._tablename) & (self.db.plugin_thumbnails.field_name == table_field.name)).delete()
        return False

    def _get_thumbnail(self, table_field, row):
        thumb = self.db((self.db.plugin_thumbnails.row_id == row[table_field._tablename].id) & (self.db.plugin_thumbnails.table_name == table_field._tablename) & (self.db.plugin_thumbnails.field_name == table_field.name)).select().first()
        if thumb is not None:
            thumb_file = thumb.image_thumbnail
        else:
            thumb_file = row[table_field._tablename].image
        return thumb_file

    def make_thumbnail(self, table_field, row_id, size=(175, 175), use_imageops=False):
        """
        Create a thumbnail of an uploaded image and insert it in thumbnail table
        :param table_field: table field object of type images
        :param row_id: id of row
        :param size: thumbnail size (x,y)
        :param use_imageops: if set true, use ImageOps.fit instead of thumbnail PIL function
        """
        table = self.db[table_field._tablename]
        try:
            from PIL import Image

            row = table(row_id)
            im = Image.open(os.path.join(current.request.folder, 'uploads', row[table_field.name]))
            if not use_imageops:
                im.thumbnail(size, Image.ANTIALIAS)
            else:
                from PIL import ImageOps
                im = ImageOps.fit(im, size, Image.ANTIALIAS)
            thumbnail_tmp_path = 'thumbnails.tmp_thumbnail_thumb.%s.jpg' % row[table_field.name].split('.')[2]
            im.save(os.path.join(current.request.folder, 'uploads', thumbnail_tmp_path), 'jpeg')
            stream = open(os.path.join(current.request.folder, 'uploads', thumbnail_tmp_path), 'rb')

            img = self.db((self.db.plugin_thumbnails.row_id == row_id) & (self.db.plugin_thumbnails.table_name == table._tablename) & (self.db.plugin_thumbnails.field_name == table_field.name)).select()
            if len(img) > 0:
                img[0].update_record(image_thumbnail=stream)
            else:
                self.db.plugin_thumbnails.insert(row_id=row_id,table_name=table._tablename, field_name=table_field.name, image_thumbnail=stream)

            os.remove(os.path.join(current.request.folder, 'uploads', thumbnail_tmp_path))
            self.db.commit()
        except:
            pass
        try:
            row = table(row_id)
            thumbnail_tmp_path = 'thumbnails.tmp_thumbnail_thumb.%s.jpg' % row[table_field.name].split('.')[2]
            os.remove(os.path.join(current.request.folder, 'uploads', thumbnail_tmp_path))
        except:
            pass