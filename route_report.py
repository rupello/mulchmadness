""" This scripts generates pdf reports from normalized data """
import os
import time

import pandas as pd
import requests
import qrcode

from motionless import DecoratedMap, AddressMarker, LatLonMarker

from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def order_report(outdir, fr_bags,i):
    reportpath = os.path.join(outdir,folder+'.pdf')
    doc = SimpleDocTemplate(reportpath,pagesize=letter,
                rightMargin=72,leftMargin=72,
                topMargin=72,bottomMargin=18)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    
    doc.build(order_content(outdir, fr_bags,i))
    
def order_content(outdir, fr_bags,i):
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))

    Story = []
    
    # make folder for maps & qr-code
    folder = '{}-{}'.format(fr_bags['Order No.'][i],fr_bags['norm_address'][i])
    folderpath = os.path.join(outdir,folder)  
    if not os.path.exists(folderpath):
        print('creating folder {}'.format(folderpath))
        os.mkdir(folderpath)
    
    maps = []
    for mapzoom in (12,16,18):
        mappath = os.path.join(folderpath,'map%d.png' % mapzoom)
        if not os.path.exists(mappath):
            downloadmap(mappath, [(fr_bags['latitude'][i],fr_bags['longitude'][i])], mapzoom)
        maps.append(mappath)
        
    qrimgpath = os.path.join(folderpath,'qrcode.png')
    if not os.path.exists(qrimgpath):
        googleqrcode(fr_bags['latitude'][i],fr_bags['longitude'][i],qrimgpath)
    

    formatted_time = time.ctime()

    ptext = '<font size=12>Generated %s</font>' % formatted_time

    Story.append(Paragraph(ptext, styles["Normal"]))
    Story.append(Spacer(1, 12))
    
    Story.append(Paragraph('Order#: {}'.format(int(fr_bags['Order No.'][i])), styles["Normal"]))
    Story.append(Paragraph('Access: {}'.format(fr_bags['truck_type'][i]), styles["Normal"]))
    Story.append(Paragraph('Address: {}'.format(fr_bags['full_address'][i]), styles["Heading1"]))
    Story.append(Paragraph('Name: {} {}'.format(fr_bags['First Name'][i],fr_bags['Last Name'][i]), styles["Heading1"]))
    Story.append(Paragraph('Bags: {}'.format(int(fr_bags['No. of Bags'][i])), styles["Heading1"]))
    Story.append(Paragraph('Notes: {}'.format(fr_bags['Notes'][i]), styles["Normal"]))
    
    Story.append(Spacer(1, 12))
        
    ims=[Image(m, 2*inch, 2*inch) for m in maps]
    
    data = [ims]
    
    table = Table(data, colWidths=2.2*inch, rowHeights=2.2*inch)
    table.setStyle(TableStyle([
                           ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                          ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                          ('BACKGROUND',(0,0),(-1,2),colors.white)
                          ]))
    Story.append(table)
    Story.append(Image(qrimgpath, 2*inch, 2*inch))
    
    return Story


def route_manifest(outdir, fr_bags, indeces, routename):
    'generates route coversheet and page for each order'
    reportpath = os.path.join(outdir,"{}-manifest.pdf".format(routename))
    doc = SimpleDocTemplate(reportpath,pagesize=letter,
                    rightMargin=72,leftMargin=72,
                    topMargin=72,bottomMargin=18)
    Story = [] 

    formatted_time = time.ctime()

    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
    ptext = '<font size=12>Generated %s</font>' % formatted_time

    Story.append(Paragraph(ptext, styles["Normal"]))
    Story.append(Spacer(1, 12))   
    Story.append(Paragraph('Manifest for route {}'.format(routename),styles["Heading1"]))
    
    data = []
    totalbags = 0
    for i in indeces:
        nbags = int(fr_bags['No. of Bags'][i])
        data.append([i,fr_bags['full_address'][i], '%d bags' % nbags])
        totalbags+=nbags
    
    table = Table(data, colWidths=[.5*inch, 3*inch,.75*inch], rowHeights=.3*inch,hAlign='LEFT')
    table.setStyle(TableStyle([
                           ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                          ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                          ('BACKGROUND',(0,0),(-1,2),colors.white)
                          ]))
    Story.append(table)    
    Story.append(Paragraph('Total: {}'.format(totalbags),styles["Normal"]))
    
    for i in indeces:
        Story.append(PageBreak())
        Story.extend(order_content(outdir,fr_bags, i))
    
    doc.build(Story)



def make_all_manifests(inputfile, outdir):
    assert(os.path.exists(outdir))
    fr = pd.read_excel(inputfile)
    fr_bags = fr[fr['No. of Bags']>0]
    gbr = fr_bags.groupby(['route_number']).groups
    for (k,rows) in gbr.items():
        if k != 'unknown':
            routedir = os.path.join(outdir,k)
            if not os.path.exists(routedir):
                print('creating folder {}'.format(routedir))
                os.mkdir(routedir)
            route_manifest(routedir, fr_bags=fr_bags, indeces=gbr[k], routename=k)
    


def static_map_url(markers,zoom=None):
    key = 'AIzaSyDpT6xnePrW02hH4XxErpTf1OV2yRu4RbQ'

    road_styles = [{
        'feature': 'road.highway',
        'element': 'geometry',
        'rules': {
            'visibility': 'simplified',
            'color': '#c280e9'
        }
    }, {
        'feature': 'transit.line',
        'rules': {
            'visibility': 'simplified',
            'color': '#bababa'
        }
    }]
    dmap = DecoratedMap(style=road_styles,zoom=zoom)
    for i,(latitude,longitude) in enumerate(markers):
        dmap.add_marker(LatLonMarker(latitude,longitude,label=chr(65+i)))
    return (dmap.generate_url()+'&key={}'.format(key))


def downloadmap(path, markers ,zoom=None):
    url = static_map_url(markers,zoom)
    r = requests.get(url)
    if r.status_code == 200:
        with open(path,'wb') as f:
            f.write(r.content)

def googlemaps_url(lat,lon):
    return "http://maps.google.com/?q={},{}".format(lat,lon)


def qrcodeim(url,path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    im = qr.make_image()
    im.save(path)

def googleqrcode(lat,lon,path):
    qrcodeim(googlemaps_url(lat,lon),path)


if __name__ == '__main__':
    outdir = './reports/'
    inputfile = './data/tracker_norm.xls'
    make_all_manifests(inputfile,outdir)

