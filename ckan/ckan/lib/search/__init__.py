import logging
import pkg_resources
from pylons import config
from common import QueryOptions, SearchError, SearchQuery, SearchBackend, SearchIndex
from worker import dispatch_by_operation

log = logging.getLogger(__name__)

DEFAULT_OPTIONS = {
    'limit': 20,
    'offset': 0,
    'filter_by_openness': False,
    'filter_by_downloadable': False,
    # about presenting the results
    'order_by': 'rank',
    'return_objects': False,
    'ref_entity_with_attr': 'name',
    'all_fields': False,
    'search_tags': True,
    'callback': None, # simply passed through
    }

# TODO make sure all backends are thread-safe! 
INSTANCE_CACHE = {}

def get_backend(backend=None):
    if backend is None:
        backend = config.get('search_backend', 'sql')
    klass = None
    for ep in pkg_resources.iter_entry_points("ckan.search", backend.strip().lower()):
        klass = ep.load()
    if klass is None:
        raise KeyError("No search backend called %s" % (backend,))
    if not klass in INSTANCE_CACHE.keys():
        log.debug("Creating search backend: %s" % klass.__name__)
        INSTANCE_CACHE[klass] = klass()
    return INSTANCE_CACHE.get(klass)

def rebuild():
    from ckan import model
    backend = get_backend()
    log.debug("Rebuilding search index...")
    
    # Packages
    package_index = backend.index_for(model.Package)
    package_index.clear()
    for pkg in model.Session.query(model.Package).all():
        package_index.insert_entity(pkg)
    model.Session.commit()

def check():
    from ckan import model
    backend = get_backend()
    package_index = backend.index_for(model.Package)

    log.debug("Checking packages search index...")
    pkgs_q = model.Session.query(model.Package).filter_by(state=model.State.ACTIVE)
    pkgs = set([pkg.id for pkg in pkgs_q])
    indexed_pkgs = set(package_index.get_all_entity_ids())
    pkgs_not_indexed = pkgs - indexed_pkgs
    print 'Packages not indexed = %i out of %i' % (len(pkgs_not_indexed), len(pkgs))
    for pkg_id in pkgs_not_indexed:
        pkg = model.Session.query(model.Package).get(pkg_id)
        print pkg.revision.timestamp.strftime('%Y-%m-%d'), pkg.name

def show(package_reference):
    from ckan import model
    backend = get_backend()
    package_index = backend.index_for(model.Package)
    print package_index.get_index(package_reference)

def query_for(_type, backend=None):
    """ Query for entities of a specified type (name, class, instance). """
    return get_backend(backend=backend).query_for(_type)

