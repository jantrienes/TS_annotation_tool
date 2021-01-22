from django.contrib import admin
from django.urls import path, include, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('settings_admin/', admin.site.urls),
    path("corpora/", views.overview, name="overview"),
    # path('overview/<str:domain>', views.overview, name='overview'),
    # path('overview/<str:domain>/<int:corpus>', views.overview, name='overview'),
    path("doc/<int:doc_pair_id>", views.overview_per_doc, name="overview_per_doc"),
    path('', include(('alignment.urls', "alignment"), namespace="alignment")),
    path('', include(('rating.urls', "rating"), namespace="rating")),
    path('evaluation/', include(('evaluation.urls', "evaluation"), namespace="evaluation")),
    path('accounts/', include(('accounts.urls', "accounts"), namespace="accounts")),
    path('data/', include(('data.urls', "data"), namespace="data")),
    path('change_log/', include(('change_log.urls', "change_log"), namespace="change_log")),
    path('simplification/', include(('simplification.urls', "simplification"), namespace="simplification")),
    path('web_scraping/', include(('web_scraping.urls', "web_scraping"), namespace="web_scraping")),
    re_path('^$', views.home, name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
