from itertools import chain

from django.core.urlresolvers import reverse
from django.forms import widgets
from django.utils.datastructures import MultiValueDict, MergeDict
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt

from .utils import combine_css_classes
from .select2 import jquery_url, select2_js_url, select2_css_url
from .views import Select2View

import logging
logger = logging.getLogger(__name__)

__all__ = ('Select', 'SelectMultiple',)


class Select(widgets.Select):
    ajax = False
    allow_multiple_selected = False

    class Media:
        js = (
            jquery_url(),
            select2_js_url()
        )
        css = (
            select2_css_url()
        )

    def __init__(self, attrs=None, choices=(), **kwargs):
        self.ajax = kwargs.pop('ajax', self.ajax)

        self.attrs = attrs or {}

        if 'overlay' in kwargs:
            self.attrs['data-placeholder'] = kwargs.pop('overlay')

        self.attrs['class'] = combine_css_classes(self.attrs.get('class', None), 'djselect2')

        self.choices = iter(choices)

    def reverse(self):
        opts = getattr(self, 'model', self.field.model)._meta
        return reverse('select2_fetch_items', kwargs={
            'app_label': opts.app_label,
            'model_name': opts.object_name.lower(),
            'field_name': self.field.name,
        })

    def get_labels(self, pks):
        opts = getattr(self, 'model', self.field.model)._meta
        view_cls = Select2View(opts.app_label, opts.object_name.lower(), self.field.name)
        return view_cls.init_selection(pks, 'multiple' in self.attrs)

    def render(self, name, value, attrs={}, choices=()):
        if 'readonly' in attrs and attrs['readonly'] != False:
            if value:
                value_text = self.get_labels([value])[0]['text']
                final_attrs = self.build_attrs(attrs, name=name, value=value, type="hidden")
                output = [format_html('<input{}>', flatatt(final_attrs))]
                value = self.get_labels([value])[0]['text']
                del final_attrs['id']
                del final_attrs['type']
                final_attrs['value'] = value_text
                final_attrs['disabled'] = 'disabled'
                output.append(format_html('<input{}>', flatatt(final_attrs)))
                return mark_safe('\n'.join(output))
            else:
                final_attrs = self.build_attrs(attrs, name=name)
                output = [format_html('<input{}>', flatatt(final_attrs))]
                return mark_safe('\n'.join(output))

        if self.ajax:
            attrs.update({
                'data-ajax--url': attrs.get('data-ajax--url', self.reverse())
            })

        final_attrs = self.build_attrs(attrs, name=name)
        output = [format_html('<select{}>', flatatt(final_attrs))]
        if not self.ajax or value is not None:
            options = self.render_options(choices, value if isinstance(value, list) else [value])
            if options:
                output.append(options)
        output.append('</select>')
        return mark_safe('\n'.join(output))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        if self.ajax:
            for option in self.get_labels(selected_choices):
                output.append(self.render_option(selected_choices, option['id'], option['text']))
        else:
            for option_value, option_label in chain(self.choices, choices):
                if isinstance(option_label, (list, tuple)):
                    output.append(format_html('<optgroup label="{}">', force_text(option_value)))
                    for option in option_label:
                        output.append(self.render_option(selected_choices, *option))
                    output.append('</optgroup>')
                else:
                    output.append(self.render_option(selected_choices, option_value, option_label))
        return '\n'.join(output)


class SelectMultiple(Select):
    allow_multiple_selected = True

    def __init__(self, attrs={}, choices=(), **kwargs):
        attrs.update({
            'multiple': 'multiple'
        })

        super(SelectMultiple, self).__init__(attrs=attrs, choices=choices, **kwargs)

    def value_from_datadict(self, data, files, name):
        # Since ajax widgets use hidden or text input fields, when using ajax the value needs to be a string.
        if isinstance(data, (MultiValueDict, MergeDict)):
            return data.getlist(name)
        return data.get(name, None)
