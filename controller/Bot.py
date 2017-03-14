from base.controller import Controller
from base.model import Model

class Bot(Controller):
    def __init__(self, *args, **kwargs):
        Controller.__init__(self, *args, **kwargs)
        self.BotModel = Model(config_file=self.config_file, db_section='default_db')

    def get_bot(self, user_id=None):
        self.BotModel.open_pool()
        self.BotModel.open_conn_cursor(self.BotModel.pool)
        self.BotModel.select(table='bot')
        if user_id:
            self.BotModel.where('id = {}'.format(user_id))
        response = self.BotModel.execute(False, False)
        self.BotModel.close_conn_cursor()
        return response