from django.forms import ModelForm
from django import forms
from . models import *

class ChatMessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body']
        labels = {
            'body':'',
        }
        widgets = {
            'body' : forms.TextInput(attrs={'placeholder': 'Add message ...', 'class': 'p-4 text-black', 'maxlength' :'300', 'autofocus': True }),
        }
        
        
class NewGroupForm(ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Members",
    )

    class Meta:
        model = ChatGroup
        fields = ['groupchat_name', 'description', 'members']
        widgets = {
            'groupchat_name': forms.TextInput(attrs={
                'placeholder': 'Add name ...',
                'class': 'p-4 text-black',
                'maxlength': '300',
                'autofocus': True,
            }),
            'description': forms.TextInput(attrs={
                'placeholder': 'Add description...',
                'class': 'p-4 text-black',
                'rows': 4,
                'maxlength': '1000',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['members'].queryset = user.profile.friends.all()  # Adjust based on your friends logic


        
        
class ChatRoomEditForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name','description']
        widgets = {
            'groupchat_name' : forms.TextInput(attrs={
                'class' : 'p-4 text-xl font-bold mb-4',
                'placeholder' : 'Add name here',
                'maxlength' : '300',
            }),
            'description' : forms.TextInput(attrs={
                'placeholder' : 'Add Decsription here',
                'class' : 'p-4 text-lg mb-4',
                'rows': 4,
                'maxlength': '1000',
                }),
        }
        
class InviteForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder' : 'Enter friend\'s email...',
            'class' : 'p-4 text-black',
        })
    )