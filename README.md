web2py-thumbnails
=================

Thumbnails plugin for the web2py framework.

This plugin allows automatic creation of thumbnails from image upload fields. It creates a virtual field and not modify original tables.


Installation
============

- Install or include Python Imaging Library (PIL)
- Download The plugin installer (.w2p file) and install it via the web2py interface.

Usage
=====

```python
# coding: utf8

db = DAL()
db.define_table('mytable',Field('myfield','string'),
                          Field('img','upload'))

from plugin_thumbnails.thumbnails import thumbnails          # imports thumbnails plugin
thumb = thumbnails(db, autodelete=True)                      # instantiate plugin and crete thumbnails table
thumb.create(db.mytable.img, (150, 150), use_imageops=True)  # create thumbnails for mytable img field

db.mytable.insert(myfield='Char',img=image)                  # automatically create thumbnail for img field
db(db.mytable.id==1).update(img=new_image)                   # automatically update thumbnail
thumbnail = db(db.mytable).select().first().img_thumbnail    # select thumbnail
db(db.mytable.id==1).delete()                                # automatically delete thumbnail

```