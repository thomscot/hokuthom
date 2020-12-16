import json
import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Union

import flask
import pandas as pd
from dateutil import parser
from flask import Flask
from flask_restful import Api, Resource, abort

from bluebear.config import BALANCE_TRACER_INFLUXDB_CONNECTION_STRING
from bluebear.script.queryman import Queryman

logger = logging.getLogger(__name__)


class TotalBalanceAsOfDate(Resource):

    @staticmethod
    def parse_moment(moment: str) -> str:
        if moment in ['now', 'today']:
            as_of_utc = datetime.now()
        else:
            as_of_utc = parser.parse(moment).replace(tzinfo=None)

        return str(as_of_utc.replace(tzinfo=None).replace(hour=22, minute=0, second=0, microsecond=0))

    @staticmethod
    def balances_to_map(balances) -> Dict[str, Union[str, Dict[str, Decimal]]]:

        df = pd.DataFrame([next(bp) for _, bp in balances.items()])
        df = df.groupby('base_ccy').agg({'balance': {'total_amount': sum}})['balance']

        # return the result
        return {ccy: amounts['total_amount'] for (ccy, amounts) in df.iterrows()}

    @staticmethod
    def get(moment: str):

        try:
            # parse the parameter
            as_of_utc = TotalBalanceAsOfDate.parse_moment(moment=moment)

            # load the data
            queryman = Queryman(os.getenv(BALANCE_TRACER_INFLUXDB_CONNECTION_STRING))
            balances = queryman.get_balances(as_of_utc)

            # massage the data and convert it into a JSON-serializable object
            json_data = {
                'as_of_utc': as_of_utc,
                'balance': TotalBalanceAsOfDate.balances_to_map(balances),
            }

            response = flask.make_response(json.dumps(json_data, indent=2, default=str))
            response.headers['content-type'] = 'application/json'

            return response

        except Exception as error:
            logger.fatal(f"Error processing data from the influxDb: {error}")
            abort(
                http_status_code=500,
                message=error,
            )


def register_rest(bb_app):
    rest_api = Api(bb_app)
    rest_api.add_resource(TotalBalanceAsOfDate, '/total_balance_as_of_date/<string:moment>')

    return bb_app


if __name__ == '__main__':
    register_rest(Flask(__name__)).run(debug=True)
