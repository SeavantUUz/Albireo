# -*- coding: utf-8 -*-
from domain.Episode import Episode
from domain.Bangumi import Bangumi
from datetime import datetime
from utils.SessionManager import SessionManager
from utils.http import json_resp
from utils.db import row2dict
from sqlalchemy.sql.expression import or_, desc, asc
from sqlalchemy.sql import select, func
import json

class AdminService:

    def __get_eps_len(self, eps):
        EPISODE_TYPE = 0 # episode type = 0 is the normal episode type, even the episode is not a 24min length
        eps_length = 0
        for eps_item in eps:
            if eps_item['type'] == EPISODE_TYPE:
                eps_length = eps_length + 1

        return eps_length

    def __get_bangumi_status(sefl, air_date):
        _air_date = datetime.strptime(air_date, '%Y-%m-%d')
        _today = datetime.today()
        if _today >= _air_date:
            return Bangumi.STATUS_ON_AIR
        else:
            return Bangumi.STATUS_PENDING


    def list_bangumi(self, page, count, sort_field, sort_order, name):

        session = SessionManager.Session()
        query_object = session.query(Bangumi)

        if name is not None:
            query_object = query_object.filter(or_(Bangumi.name==name, Bangumi.name_cn==name))
            # count total rows
            total = session.query(func.count(Bangumi.id)).filter(or_(Bangumi.name==name, Bangumi.name_cn==name)).scalar()
        else:
            total = session.query(func.count(Bangumi.id)).scalar()

        offset = (page - 1) * count

        if(sort_order == 'desc'):
            bangumi_list = query_object.order_by(desc(getattr(Bangumi, sort_field))).offset(offset).limit(count).all()
        else:
            bangumi_list = query_object.order_by(asc(getattr(Bangumi, sort_field))).offset(offset).limit(count).all()

        bangumi_dict_list = [row2dict(bangumi) for bangumi in bangumi_list]

        SessionManager.Session.remove()

        return json_resp({'data': bangumi_dict_list, 'total': total})


    def add_bangumi(self, content):
        try:
            bangumi_data = json.loads(content)

            bangumi = Bangumi(bgm_id=bangumi_data['bgm_id'],
                              name=bangumi_data['name'],
                              name_cn=bangumi_data['name_cn'],
                              summary=bangumi_data['summary'],
                              eps=bangumi_data['eps'],
                              image=bangumi_data['image'],
                              air_date=bangumi_data['air_date'],
                              air_weekday=bangumi_data['air_weekday'],
                              status=self.__get_bangumi_status(bangumi_data['air_date']))

            if 'rss' in bangumi_data:
                bangumi.rss = bangumi_data['rss']

            if 'eps_regex' in bangumi_data:
                bangumi.eps_regex = bangumi_data['eps_regex']

            session = SessionManager.Session()

            session.add(bangumi)

            bangumi.episodes = []

            for eps_item in bangumi_data['episodes']:
                eps = Episode(bgm_eps_id=eps_item['bgm_eps_id'],
                              episode_no=eps_item['episode_no'],
                              name=eps_item['name'],
                              name_cn=eps_item['name_cn'],
                              duration=eps_item['duration'],
                              airdate=eps_item['airdate'],
                              status=Episode.STATUS_NOT_DOWNLOADED)
                eps.bangumi = bangumi
                bangumi.episodes.append(eps)

            session.commit()

            bangumi_id = str(bangumi.id)

            SessionManager.Session.remove()

            return json_resp({'data': {'id': bangumi_id}})
        except Exception as exception:
            raise exception
            # resp = make_response(jsonify({'msg': 'error'}), 500)
            # resp.headers['Content-Type'] = 'application/json'
            # return resp


    def update_bangumi(self, id, bangumi_dict):
        try:
            session = SessionManager.Session()
            bangumi = session.query(Bangumi).filter(Bangumi.id == id).one()

            bangumi.name = bangumi_dict['name']
            bangumi.name_cn = bangumi_dict['name_cn']
            bangumi.summary = bangumi_dict['summary']
            bangumi.eps = bangumi_dict['eps']
            bangumi.eps_regex = bangumi_dict['eps_regex']
            bangumi.image = bangumi_dict['image']
            bangumi.air_date = datetime.strptime(bangumi_dict['air_date'], '%Y-%m-%d')
            bangumi.air_weekday = bangumi_dict['air_weekday']
            bangumi.rss = bangumi_dict['rss']
            bangumi.update_time = datetime.now()

            session.commit()

            SessionManager.Session.remove()

            return json_resp({'msg':'ok'})
        except Exception as exception:
            raise exception

    def get_bangumi(self, id):
        try:
            session = SessionManager.Session()
            bangumi = session.query(Bangumi).filter(Bangumi.id == id).one()

            bangumi_dict = row2dict(bangumi)

            SessionManager.Session.remove()

            return json_resp({'data': bangumi_dict})
        except Exception as exception:
            raise exception

    def delete_bangumi(self, id):
        try:
            session = SessionManager.Session()

            bangumi = session.query(Bangumi).filter(Bangumi.id == id).one()

            session.delete(bangumi)

            session.commit()

            SessionManager.Session.remove()

            return json_resp({'msg': 'ok'})
        except Exception as exception:
            raise exception

    def get_bangumi_from_bgm_id_list(self, bgm_id_list):
        s = select([Bangumi.id, Bangumi.bgm_id]).where(Bangumi.bgm_id.in_(bgm_id_list)).select_from(Bangumi)
        return SessionManager.engine.execute(s).fetchall()

admin_service = AdminService()