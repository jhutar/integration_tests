# -*- coding: utf-8 -*-
import attr
from cached_property import cached_property

from navmazing import NavigateToAttribute, NavigateToSibling
from wrapanapi.containers.route import Route as ApiRoute

from cfme.common import WidgetasticTaggable, TagPageView
from cfme.containers.provider import (Labelable, ContainerObjectAllBaseView,
    ContainerObjectDetailsBaseView, GetRandomInstancesMixin)
from cfme.modeling.base import BaseCollection, BaseEntity
from cfme.utils.appliance.implementations.ui import navigator, CFMENavigateStep
from cfme.utils.providers import get_crud_by_name


class RouteAllView(ContainerObjectAllBaseView):
    SUMMARY_TEXT = "Routes"


class RouteDetailsView(ContainerObjectDetailsBaseView):
    pass


@attr.s
class Route(BaseEntity, WidgetasticTaggable, Labelable):

    PLURAL = 'Routes'
    all_view = RouteAllView
    details_view = RouteDetailsView

    name = attr.ib()
    project_name = attr.ib()
    provider = attr.ib()

    @cached_property
    def mgmt(self):
        return ApiRoute(self.provider.mgmt, self.name, self.project_name)


@attr.s
class RouteCollection(GetRandomInstancesMixin, BaseCollection):
    """Collection object for :py:class:`Route`."""

    ENTITY = Route

    def all(self):
        # container_routes table has ems_id, join with ext_mgmgt_systems on id for provider name
        # Then join with container_projects on the id for the project
        route_table = self.appliance.db.client['container_routes']
        ems_table = self.appliance.db.client['ext_management_systems']
        project_table = self.appliance.db.client['container_projects']
        route_query = (
            self.appliance.db.client.session
                .query(route_table.name, project_table.name, ems_table.name)
                .join(ems_table, route_table.ems_id == ems_table.id)
                .join(project_table, route_table.container_project_id == project_table.id))
        provider = None
        # filtered
        if self.filters.get('provider'):
            provider = self.filters.get('provider')
            route_query = route_query.filter(ems_table.name == provider.name)
        routes = []
        for name, project_name, ems_name in route_query.all():
            routes.append(self.instantiate(name=name, project_name=project_name,
                                           provider=provider or get_crud_by_name(ems_name)))

        return routes


@navigator.register(RouteCollection, 'All')
class All(CFMENavigateStep):
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')
    VIEW = RouteAllView

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Containers', 'Routes')

    def resetter(self):
        # Reset view and selection
        self.view.toolbar.view_selector.select("List View")
        self.view.paginator.reset_selection()


@navigator.register(Route, 'Details')
class Details(CFMENavigateStep):
    prerequisite = NavigateToAttribute('parent', 'All')
    VIEW = RouteDetailsView

    def step(self):
        self.prerequisite_view.entities.get_entity(name=self.obj.name,
                                                   project_name=self.obj.project_name,
                                                   use_search=True).click()


@navigator.register(Route, 'EditTags')
class ImageRegistryEditTags(CFMENavigateStep):
    VIEW = TagPageView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.toolbar.policy.item_select('Edit Tags')
