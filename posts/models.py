from django.contrib.auth import get_user_model
from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Text', help_text='Write a text')
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts'
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, blank=True, null=True,
        related_name='posts', verbose_name='Group',
        help_text='Choose a group'
    )
    image = models.ImageField(storage=S3Boto3Storage(location='media'), blank=True, null=True)

    class Meta:
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments'
    )
    text = models.TextField(verbose_name='Текст')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    def __str__(self):
        return f'Follower: {self.user}, Favourite author: {self.author}'
