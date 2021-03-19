import requests
import json
import copy
import operator
from itertools import islice
from .dict_parse import search_parse, food_parse
from ..objects.nutrient_dict import nutrient_dict

class SearchResults():
    """
    An object returned by Client.search_query which stores a Python dictionary
    containing all of the search result information.
    """
    def __init__(self, json):
        self.json = json
        print('I am here')
    def __str__(self, max_entries=None):
        print('__str__')
        r_str = ""
        if self.json == None:
            r_str += "There are no search results for this query\n"
        else:
            r_str +="="*112 + "\n"
            r_str +="Search results for \'{}\' on USDA Standard Reference Database".format(self.json["search_term"]) + "\n"
            r_str +="="*112 + "\n"
            print('yes')
            #raise Exception
            if max_entries == None:
                max_entries = len(self.json["items"])
            if max_entries < len(self.json["items"]):
                self.json["items"] = self.json["items"][:max_entries]
            # hack feb252021
            #self.json["items"].sort(key=operator.itemgetter("group"))
            self.json["items"].sort(key=operator.itemgetter("dataType"))
            #raise Exception
            r_str +="{name:<72} {group:^30} {id:>8}".format(name="description",group="dataType",id="ID") + "\n"
            for item in self.json["items"]:
                if len(item["description"]) > 70:
                    item["description"] = item["description"][:70] + ".."
                if len(item["dataType"]) > 28:
                    item["dataType"] = item["dataType"][:28] + ".."
                r_str +="{name:<72} {group:^30} {id:>8}".format(name=item["description"],group=item["dataType"],id=item["fdcId"]) + "\n"
            r_str +="="*112 + "\n"
        return r_str

class Client:
    """
    The Client class is used to interface with the USDA Standard Reference Database
    API. It must be initialized with an API key.
    """

    #url = 'https://api.nal.usda.gov/usda/ndb'
    url = 'https://api.nal.usda.gov/fdc/v1/foods'


    def __init__(self, key):
        """
        A Client instance must be initialized with a key from
        data.gov. This is free to obtain, and you can request one
        here: https://api.data.gov/signup/
        """
        self.key = key

    def call(self, params, url_suffix):
        """ target_url could be:
        https://api.nal.usda.gov/usda/ndb/V2/reports
        https://api.nal.usda.gov/usda/ndb/search
        depending on which service of the api is being used
        """
        #print(self.url)
        target_url = self.url + url_suffix 
        print("****target_url***", target_url)
        # add the key to the API call
        call_params = dict(params, api_key=self.key)
        #print(call_params)
        test_response = requests.get(url=target_url, params=call_params)
        #print('test_response', test_response)
        print(test_response.url)
        response = json.loads(requests.get(url=target_url, params=call_params).text)
        print(response)
        #print(type(response))
        #import shelve
        #db=shelve.open('pantry.shelve')
        ##print(params['query'], response['foods'][0]['fdcId'], response['foods'][0]['ndbNumber'])
        #print(params['query'], response['foods'][0]['fdcId'])

        #db[str(response['foods'][0]['fdcId'])] = params['query']
        #db.close()
        #eRRr= input('error happened: ')
        import pickle
        pickle.dump(response, open('response.pkl', 'wb'))
        return response

    def search_query(self, name):
        #import numpy
        params = dict(
            query=name,
            requireAllWords=True,
            #dataType = {'Foundation':1}
            dataType=['Foundation', 'Survey (FNDDS)', 'SR Legacy']#{'Branded':0}
            #ds='Standard Reference',
            #format='json'
        )
        return SearchResults(search_parse(self.call(params, '/search')))
    
    def food_query(self, ids):
        # allow for either a single id (ndbno) query, or a list of queries
        if type(ids) == list:
            if len(ids) > 25:
                raise Exception("Too many Food ID arguments. API limits it to 25.")
        #params = dict(ndbno=ids)
        params = dict(fdcIds=ids)
        #params = dict(ndbNumber=ids)
        #params.update(dict(type='f', format='json'))
#        return_obj = self.call(params, '/V2/reports')
        return_obj = self.call(params, '')
        print(return_obj)
        #raise Exception
        offset = 0

        #if 'foods' not in return_obj:
        if 'error' in return_obj:
            print("See the following error: {}".format(return_obj))
            exit()
        #raise Exception('test')
        #for i in range(0, len(return_obj["foods"])):
        #    if 'error' in return_obj["foods"][i-offset].keys():
        #        del return_obj["foods"][i-offset]
        #        offset += 1
        return return_obj

    def get_foods(self, id_value_dict):
        # If more than 25 words are being queried, split it up
        if len(id_value_dict.keys()) > 25:
            print("Must call the database {} times, this may take a couple moments. Status: {leng}/{leng}".format(len(id_value_dict.keys())//25+1,leng=len(id_value_dict.keys())))
            dict_copy = id_value_dict.copy()
            food_obj = []
            while len(dict_copy.keys()) > 25:
                current_dict = {}
                items = islice(dict_copy.items(), 25)
                current_dict.update(items)
                call = self.food_query(current_dict.keys())
                food_obj += food_parse(call, nutrient_dict, list(current_dict.values()))
                for key in current_dict.keys():
                    del dict_copy[key]
                print("Status: {}/{}".format(len(dict_copy.keys()), len(id_value_dict.keys())))
            call = self.food_query(dict_copy.keys())
            food_obj += food_parse(call, nutrient_dict, list(dict_copy.values()))
            print("Complete!")
        else:
            food_obj = self.food_query(id_value_dict.keys())
            food_obj = food_parse(food_obj, nutrient_dict, list(id_value_dict.values()))
        return food_obj
