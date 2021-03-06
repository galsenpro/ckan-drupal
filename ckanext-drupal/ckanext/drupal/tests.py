from ckan.lib.create_test_data import CreateTestData
import ckan.model as model
from ckan.tests import WsgiAppCase
import json
from ckan import plugins
from pprint import pprint, pformat
from pylons import config
from sqlalchemy import MetaData, create_engine, Table

class TestAction(WsgiAppCase):

    @classmethod
    def setup_class(cls):
        model.repo.rebuild_db()
        CreateTestData.create()
        plugins.load('drupal')
        from ckan.plugins import PluginImplementations
        from ckan.plugins.interfaces import IConfigurer
        for plugin in PluginImplementations(IConfigurer):
            plugin.update_config(config)

        url = config['drupal.db_url'] 
        cls.engine = create_engine(url, echo=True)
        cls.metadata = MetaData(cls.engine)
        cls.node = Table('node',
                          cls.metadata,
                          autoload = True)
        cls.node = Table('node_revisions',
                          cls.metadata,
                          autoload = True)
        cls.package_table = Table('ckan_package',
                                  cls.metadata,
                                  autoload = True)
        cls.extra_table = Table('ckan_package_extra',
                                  cls.metadata,
                                  autoload = True)
        cls.resource_table = Table('ckan_resource',
                                  cls.metadata,
                                  autoload = True)
        cls.engine.execute('delete from ckan_package')
        cls.engine.execute('delete from ckan_resource')
        cls.engine.execute('delete from ckan_package_extra')
        cls.engine.execute('delete from ckan_package_tag')
        cls.engine.execute('delete from node')
        cls.engine.execute('delete from node_revisions')

    def test_00_migrate_data(self):

        apikey = model.User.get('testsysadmin').apikey
        postparams = '%s=1' % json.dumps({})
        res = self.app.post('/api/action/migrate_data', params=postparams,
                            extra_environ={'Authorization': str(apikey)}, status=200)
        conn = self.engine.connect()

        package_count = conn.execute('select count(*) from ckan_package').fetchone()
        res_count = conn.execute('select count(*) from ckan_resource').fetchone()
        extra_count = conn.execute('select count(*) from ckan_package_extra').fetchone()
        tag_count = conn.execute('select count(*) from ckan_package_tag').fetchone()
        assert package_count[0] == 2
        assert res_count[0] == 2
        assert extra_count[0] == 2
        assert tag_count[0] == 3

    def test_01_create_update_package(self):

        package = {
            'nid': 1,
            'author': None,
            'author_email': None,
            'extras': [{'key': u'original media','value': u'"book"'}],
            'license_id': u'other-open',
            'maintainer': None,
            'maintainer_email': None,
            'name': u'moo1',
            'notes': u'Some test now',
            'resources': [{'alt_url': u'alt123',
                           'description': u'Full text.',
                           'extras': {u'alt_url': u'alt123', u'size': u'123'},
                           'format': u'plain text',
                           'hash': u'abc123',
                           'position': 0,
                           'url': u'http://www.annakarenina.com/download/'},
                          {'alt_url': u'alt345',
                           'description': u'Index of the novel',
                           'extras': {u'alt_url': u'alt345', u'size': u'345'},
                           'format': u'json',
                           'hash': u'def456',
                           'position': 1,
                           'url': u'http://www.annakarenina.com/index.json'}],
            'tags': [{'name': u'russian'}, {'name': u'tolstoy'}],
            'title': u'A Novel By Tolstoy',
            'url': u'http://www.annakarenina.com',
            'version': u'0.7a'
        }

        wee = json.dumps(package)
        postparams = '%s=1' % json.dumps(package)
        res = self.app.post('/api/action/drupal_package_create', params=postparams,
                            extra_environ={'Authorization': 'tester'})
        package_created = json.loads(res.body)['result']

        conn = self.engine.connect()
        package_count = conn.execute('select count(*) from ckan_package').fetchone()
        res_count = conn.execute('select count(*) from ckan_resource').fetchone()
        extra_count = conn.execute('select count(*) from ckan_package_extra').fetchone()
        tag_count = conn.execute('select count(*) from ckan_package_tag').fetchone()
        assert package_count[0] == 3
        assert res_count[0] == 4
        assert extra_count[0] == 3
        assert tag_count[0] == 5

        package_created['name'] = 'moo2'
        package_created['tags'] = [{'name': u'russian'}]

        postparams = '%s=1' % json.dumps(package_created)
        res = self.app.post('/api/action/drupal_package_update', params=postparams,
                            extra_environ={'Authorization': 'tester'})

        tag_count = conn.execute('select count(*) from ckan_package_tag').fetchone()
        assert tag_count[0] == 4

        package_updated = json.loads(res.body)['result']
        package_updated.pop('revision_id')
        package_updated.pop('revision_timestamp')
        package_updated.pop('revision_message')
        package_updated['tags'][0].pop('id')
        package_updated['tags'][0].pop('revision_timestamp')
        package_updated['tags'][0].pop('state')
        package_created.pop('revision_id')
        package_created.pop('revision_timestamp')
        package_created.pop('revision_message')
        pprint(package_updated)
        pprint(package_created)
        assert package_updated == package_created#, (pformat(json.loads(res.body)), pformat(package_created['result']))

    def test_02_create_validation_error(self):

        package = {
            'nid': 2,
            'vid': 2,
            'author': None,
            'author_email': None,
            'license_id': u'other-open',
            'maintainer': None,
            'maintainer_email': None,
            'name': u'moo1 fdsfsfsafds',
            'notes': u'Some test now',
            'title': u'A Novel By Tolstoy',
            'url': u'http://www.annakarenina.com',
            'version': u'0.7a'
        }

        wee = json.dumps(package)
        postparams = '%s=1' % json.dumps(package)
        res = self.app.post('/api/action/package_create_validate', params=postparams,
                            extra_environ={'Authorization': 'tester'}, status=409)
        error = json.loads(res.body)['error']

        assert error ==  {u'__type': u'Validation Error', u'name': [u'Name must be purely lowercase alphanumeric (ascii) characters and these symbols: -_']}, error

    def test_03_update_validation_error(self):

        id = model.Package.get('moo2').id

        package = {
            'nid': 2,
            'vid': 2,
            'id': id,
            'author': None,
            'author_email': None,
            'license_id': u'other-open',
            'maintainer': None,
            'maintainer_email': None,
            'name': u'moo1 fdsfsfsafds',
            'notes': u'Some test now',
            'title': u'A Novel By Tolstoy',
            'url': u'http://www.annakarenina.com',
            'version': u'0.7a'
        }

        wee = json.dumps(package)
        postparams = '%s=1' % json.dumps(package)
        res = self.app.post('/api/action/package_update_validate', params=postparams,
                            extra_environ={'Authorization': 'tester'}, status=409)
        error = json.loads(res.body)['error']

        assert error ==  {u'__type': u'Validation Error', u'name': [u'Name must be purely lowercase alphanumeric (ascii) characters and these symbols: -_']}


    def test_04_purge(self):

        package = model.Package.get('moo2')
        package.purge()
        model.Session.commit()


    def test_05_create_using_drupal(self):

        package = {
            'author': None,
            'author_email': None,
            'extras': [{'key': u'original media','value': u'"book"'}],
            'license_id': u'other-open',
            'maintainer': None,
            'maintainer_email': None,
            'name': u'moo1',
            'notes': u'Some test now',
            'resources': [{'alt_url': u'alt123',
                           'description': u'Full text.',
                           'extras': {u'alt_url': u'alt123', u'size': u'123'},
                           'format': u'plain text',
                           'hash': u'abc123',
                           'position': 0,
                           'url': u'http://www.annakarenina.com/download/'},
                          {'alt_url': u'alt345',
                           'description': u'Index of the novel',
                           'extras': {u'alt_url': u'alt345', u'size': u'345'},
                           'format': u'json',
                           'hash': u'def456',
                           'position': 1,
                           'url': u'http://www.annakarenina.com/index.json'}],
            'tags': [{'name': u'russian'}, {'name': u'tolstoy'}],
            'title': u'A Novel By Tolstoy',
            'url': u'http://www.annakarenina.com',
            'version': u'0.7a'
        }

        wee = json.dumps(package)
        postparams = '%s=1' % json.dumps(package)
        res = self.app.post('/api/action/package_create', params=postparams,
                            extra_environ={'Authorization': 'tester'})
        package_created = json.loads(res.body)
        assert package_created['success']

        conn = self.engine.connect()

        node = conn.execute('select * from node order by nid desc').fetchone()
        assert node['title'] == package['title']

        node_revision = conn.execute('select * from node_revisions order by vid desc').fetchone()
        assert package['title'] == node_revision['title']
        assert package['notes'] == node_revision['body']

    def test_06_purge(self):

        id = model.Package.get('moo1').id

        postparams = '%s=1' % json.dumps(dict(id=id))
        res = self.app.post('/api/action/package_purge', params=postparams,
                            extra_environ={'Authorization': 'tester'}, status=403)
        error = json.loads(res.body)['error']
        assert error == {u'message': u'Access denied', u'__type': u'Authorization Error'} 

        apikey = model.User.get('testsysadmin').apikey

        postparams = '%s=1' % json.dumps(dict(id=id))
        res = self.app.post('/api/action/package_purge', params=postparams,
                            extra_environ={'Authorization': str(apikey)}, status=200)

    def test_07_create_mistake_drupal(self):

        package = {
            'name': u'moo fdfaaasf',
            'title': u'moo fdfaaasf',
        }
        wee = json.dumps(package)
        postparams = '%s=1' % json.dumps(package)
        res = self.app.post('/api/action/package_create', params=postparams,
                            extra_environ={'Authorization': 'tester'}, status=409)
        package_created = json.loads(res.body)
        assert not package_created['success']

        conn = self.engine.connect()

        node_count = conn.execute('select count(*) from node').fetchone()

        node_revision_count = conn.execute('select count(*) from node_revisions').fetchone()

        assert node_count[0] == 2, node_count[0]
        assert node_revision_count[0] == 2, node_revision_count[0]


