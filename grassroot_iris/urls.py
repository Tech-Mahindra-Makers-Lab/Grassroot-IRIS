from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('iris_app.api_urls')),
    path('', include('iris_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
