from django.conf.urls import url
from django.contrib.admin import AdminSite, autodiscover

from .testapp.models import DemoModel

autodiscover()


class PublicAdminSite(AdminSite):
    def has_permission(self, request):
        from django.contrib.auth.models import User
        request.user = User.objects.get_or_create(username='admin')[0]
        return True


public_site = PublicAdminSite()
public_site.register(DemoModel)

urlpatterns = (
    url(r'', public_site.urls),
)
