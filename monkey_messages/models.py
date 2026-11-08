from django.db import models

#-----------------------------------------------------------------------------
# basic model with text, date, and image/base64 for sending pictures
#-----------------------------------------------------------------------------
class Monkey_Message(models.Model):
    text = models.TextField()
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    image_base64 = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # order by id to always have newest first
    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"Message {self.id}: {self.text[:30]}"
