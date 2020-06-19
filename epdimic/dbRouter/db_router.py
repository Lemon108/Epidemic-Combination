class DatabaseAppsRouter(object):
    db_app_map = {
        'Group07': 'db1',
        'users': 'default',
        'news': 'db_g6',
        'Group08': 'db1',
        'Group09': 'db1',

        'app名2': '数据库别名2'
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.db_app_map:
            return self.db_app_map[model._meta.app_label]
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.db_app_map:
            return self.db_app_map[model._meta.app_label]
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        if db == '数据库别名':
            return False
        elif db in self.db_app_map.values():
            return True
        elif app_label in self.db_app_map:
            return False
        return None
