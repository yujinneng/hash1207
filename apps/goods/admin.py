from django.contrib import admin
from goods.models import GoodsType,IndexPromotionBanner
from django.core.cache import cache

# Register your models here.

class IndexPromotionBannerAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request,obj,form,change)
        #发出任务，让celery生成首页静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        cache.delete('index_page_data')


    def delete_model(self, request, obj):
        super().delete_model(request,obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        cache.delete('index_page_data')
admin.site.register(GoodsType)
admin.site.register(IndexPromotionBanner,IndexPromotionBannerAdmin)
