from django.contrib import admin

from .models import Job, Skill, ParsedProfile, ProfilToParse, ProfilJob, JobSkill


class NameScrapperAdmin(object):
    fields = ('name',)
    list_display = ('name',)
    search_fields = ('name',)


class URLScrapperAdmin(object):
    fields = ('url',)
    list_display = ('url',)
    search_fields = ('url',)


@admin.register(Job)
class JobAdmin(NameScrapperAdmin, admin.ModelAdmin):
    pass


@admin.register(Skill)
class SkillAdmin(NameScrapperAdmin, admin.ModelAdmin):
    pass


@admin.register(ParsedProfile)
class ParsedProfileAdmin(URLScrapperAdmin, admin.ModelAdmin):
    pass


@admin.register(ProfilToParse)
class ProfilToParseAdmin(URLScrapperAdmin, admin.ModelAdmin):
    pass


@admin.register(ProfilJob)
class ProfilJobAdmin(admin.ModelAdmin):
    list_display = ['get_profil', 'get_job']

    def get_job(self, obj):
        return obj.job.name

    def get_profil(self, obj):
        return obj.profil.url


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    model = JobSkill
    list_display = ['get_job', 'get_skill', ]

    def get_job(self, obj):
        return obj.job.name

    def get_skill(self, obj):
        return obj.skill.name
