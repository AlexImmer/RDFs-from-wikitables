from django.contrib import admin
from .models import *

class RDFInline(admin.TabularInline):
    model = RDF
    extra = 0

class TableAdmin(admin.ModelAdmin):
    inlines = [RDFInline,]

class TableInline(admin.TabularInline):
    model = Table
    extra = 0

class PageAdmin(admin.ModelAdmin):
    inlines = [TableInline,]

class RDFAdmin(admin.ModelAdmin):
    list_display = ['rdf_subject', 'rdf_predicate', 'rdf_object', 'relative_occurency']
    ordering = ['relative_occurency',]

admin.site.register(Page, PageAdmin)
admin.site.register(RDF, RDFAdmin)
admin.site.register(Table, TableAdmin)
