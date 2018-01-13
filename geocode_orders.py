"""this script normalizes the address and geocodes the data using google maps api"""
import os
import pandas as pd
import googlemaps

def longify(name):
    lookups = {
        'cir' : 'circle',
        'ct' : 'court',
        'rd' : 'road',
        'dr' : 'drive',
        'pl' : 'place',
        'ln' : 'lane',
        'st' : 'street',
        'av' : 'avenue',
        'ave' : 'avenue',
    }
    if name in lookups:
        return lookups[name]
    else:
        return name

def normalize_addr(addr):
    try:
        fields = [s.strip().lower() for s in addr.split()] 
        fields[-1] = longify(fields[-1])
        return ' '.join(fields)
    except:
        return "normalize error:{}".format(addr)

def geocode(address):
    try:
        print("geocoding {}...".format(address))
        apikey = 'AIzaSyDpT6xnePrW02hH4XxErpTf1OV2yRu4RbQ'
        gmaps = googlemaps.Client(key=apikey)
        geocode_result = gmaps.geocode(address)
        return (geocode_result[0]['geometry']['location']['lat'],
               geocode_result[0]['geometry']['location']['lng'])
    except:
        print('geocoding failed for address {}'.format(address))


def geocode_addresses(fr):
    location_by_address = {}
    for a in fr['full_address']:
        location_by_address[a] = geocode(a)
    return location_by_address


if __name__ == '__main__':

    master = './data/MASTER Mulch Database_17.xls'
    tracker = './data/Sales tracker_2017.xlsx'

    assert os.path.exists(master)
    assert os.path.exists(tracker)

    fr_mast = pd.read_excel(master)
    fr_trck = pd.read_excel(tracker)

    fr_trck['norm_address'] = [normalize_addr(a) for a in fr_trck['Address']]
    fr_mast['norm_address'] = [normalize_addr(a) for a in fr_mast['address']]

    print("\n*** tracker address not in master ***")
    master_addr = set(fr_mast['norm_address'])

    fr_trck_nonzero = fr_trck[fr_trck['No. of Bags'] > 0]

    for addr in fr_trck_nonzero['norm_address']:
        if addr not in master_addr:
            print(addr)

    print("\n*** master address not in tracker ***")
    tracker_addr = set(fr_trck['norm_address'])

    fr_2017 = fr_mast[fr_mast['bags17'] > 0]

    for addr in fr_2017['norm_address']:
        if addr not in tracker_addr:
            print(addr)

    # add pipestem info to the tracker
    pipestem_address = set()
    for i in fr_mast.index:
        if str(fr_mast['  Pipestem  '][i]).strip().lower() == 'yes':
            pipestem_address.add(fr_mast['norm_address'][i])

    fr_trck['pipestem'] = [addr in pipestem_address for addr in fr_trck['norm_address']]

    # add full address field to tracker
    full_address = []
    for i in fr_trck.index:
        full_address.append('{},{},VA'.format(fr_trck['Address'][i].strip(), fr_trck['City'][i].strip()))

    fr_trck['full_address'] = full_address

    # geocode data
    locns = geocode_addresses(fr_trck)
    fr_trck['latitude'] = [locns[a][0] for a in fr_trck['full_address']]
    fr_trck['longitude'] = [locns[a][1] for a in fr_trck['full_address']]

    # default all truck_type to 'pickup'
    fr_trck['truck_type'] = ['pickup' for a in fr_trck['full_address']]

    # default route is unknown
    fr_trck['route_number'] = ['unknown' for a in fr_trck['full_address']]

    # save to excel
    print("saving normalized data to ./data/tracker_norm.xls")
    fr_trck.to_excel('./data/tracker_norm.xls')

