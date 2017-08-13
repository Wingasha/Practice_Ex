from django import forms


class SearchForm(forms.Form):
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}))
    date = forms.DateField(input_formats=('%d/%m/%Y',), widget=forms.TextInput(attrs={'class': 'form-control',
                                                                                      'readonly':'readonly'}))
