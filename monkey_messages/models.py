from django.db import models

#-----------------------------------------------------------------------------
# basic model with only text and date fields
#-----------------------------------------------------------------------------
class Monkey_Message(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id}: {self.text[:30]}"
