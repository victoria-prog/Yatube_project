from django.forms import ModelForm, Textarea

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image')


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    widgets = {'text': Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Введите комментарий'})
    }
