from django.db import models


class User(models.Model):
    name = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    campus = models.CharField(max_length=50)
    tg_id = models.IntegerField(unique=True)
    start = models.IntegerField()
    stage = models.IntegerField()
    tries = models.IntegerField(default=0) 
    score = models.IntegerField(default=0)
    wave = models.IntegerField()

    def __str__(self):
        return f'{self.name} {self.surname}'
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Question(models.Model):
    number = models.IntegerField(unique=True)
    text = models.CharField(max_length=500)
    answer = models.CharField(max_length=500)
    place_miem = models.CharField(max_length=500, blank=True)
    place_pokrovka = models.CharField(max_length=500, blank=True)
    place_basmach = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return f'{self.text}'

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'


class Game(models.Model):
    wave = models.IntegerField()
    start_question = models.IntegerField()

    def __str__(self):
        return f'{self.wave} волна'
    
    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'