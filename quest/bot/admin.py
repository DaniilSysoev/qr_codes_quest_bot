from django.contrib import admin
from .models import User, Question, Game


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'surname', 'campus', 'tg_id', 'score')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('number', 'text', 'answer', 'place_miem', 'place_pokrovka', 'place_basmach')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('wave', 'start_question')