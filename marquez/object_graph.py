"""Object Graph"""
from contextlib import contextmanager

from marquez.configuration import Configuration
from marquez.errors import CyclicGraphError, LockedGraphError
from marquez.decorators import get_defaults
from marquez.loaders import load_from_python_file
from marquez.metadata import Metadata
from marquez.registry import _registry


RESERVED = object()


class ObjectGraph(object):
    """
    An object graph contains all of the instantiated components for a microservice.

    Because components can reference each other acyclically, this collection of
    components forms a directed acyclic graph.

    """
    def __init__(self, metadata, config, registry):
        self.metadata = metadata
        self.config = config
        self._locked = False
        self._registry = registry
        self._components = {}

    def use(self, *keys):
        """
        Explicitly initialize a set of components by their binding keys.

        """
        return [
            getattr(self, key)
            for key in keys
        ]

    def lock(self):
        """
        Lock the graph so that new components cannot be created.

        """
        self._locked = True

    def unlock(self):
        """
        Unlock the graph so that new components can created.

        """
        self._locked = False

    def __getattr__(self, key):
        """
        Access a component by its binding key.

        If the component is not present, it will be lazily created.

        :raises CyclicGraphError: if the factory function requires a cycle
        :raises LockedGraphError: if the graph is locked

        """
        try:
            component = self._components[key]
            if component is RESERVED:
                raise CyclicGraphError()
            return component
        except KeyError:
            if self._locked:
                raise LockedGraphError()
            return self._resolve_key(key)

    @contextmanager
    def _reserve(self, key):
        """
        Reserve a component's binding temporarily.

        Protects against cycles.

        """
        self._components[key] = RESERVED
        try:
            yield
        finally:
            del self._components[key]

    def _resolve_key(self, key):
        """
        Attempt to lazily create a component.

        :raises NotBoundError: if the component does not have a bound factory
        :raises CyclicGraphError: if the factory function requires a cycle
        :raises LockedGraphError: if the graph is locked
        """
        with self._reserve(key):
            factory = self._registry.resolve(key)
            component = factory(self)

        self._components[key] = component
        return component


def create_object_graph(name, debug=False, testing=False, loader=load_from_python_file, registry=_registry):
    """
    Create a new object graph.

    :param name: the name of the microservice
    :param debug: is development debugging enabled?
    :param testing: is unit testing enabled?
    :param loader: the configuration loader to use
    :param registry: the registry to use (defaults to the global)
    """
    metadata = Metadata(
        name=name,
        debug=debug,
        testing=testing,
    )

    config = Configuration({
        key: get_defaults(value)
        for key, value in registry.all.items()
    })
    config.merge(loader(metadata))

    return ObjectGraph(
        metadata=metadata,
        config=config,
        registry=registry,
    )