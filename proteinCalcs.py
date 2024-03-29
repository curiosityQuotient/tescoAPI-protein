
########### Python 2.7 #############
import httplib, urllib, base64
import json

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': 'insert Key here',
}

params = urllib.urlencode({
})
query = 'tesco'
offset = 0
limit = 100
pages = 50

try:
    conn = httplib.HTTPSConnection('dev.tescolabs.com')
    conn.request("GET", "/grocery/products/?query="+query+"&offset="+str(offset)+"&limit="+str(limit)+"&%s" % params, "{body}", headers)
    response = conn.getresponse()
    data = response.read()
    DATA = json.loads(data)
    #print(data)
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))

for i in range(pages):
    offset = 100*(i+1)

    try:
        conn = httplib.HTTPSConnection('dev.tescolabs.com')
        conn.request("GET", "/grocery/products/?query="+query+"&offset="+str(offset)+"&limit="+str(limit)+"&%s" % params, "{body}", headers)

        response = conn.getresponse()
        data = response.read()
        NEWDATA = json.loads(data)
        DATA['uk']['ghs']['products']['results'].extend(NEWDATA['uk']['ghs']['products']['results'])
        conn.close()
    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))

####################################
# Retrieve data based on TPNB numbers
# create list of tpnb
tpnbList = []
for i in range(len(DATA['uk']['ghs']['products']['results'])):
    tpnbList.append(DATA['uk']['ghs']['products']['results'][i]['tpnb'])
print len(tpnbList)
#print len(set(tpnbList)) #Check that entries are unique
# Request product data
params = urllib.urlencode({
    # Request parameters
    #'gtin': '{string}',
    'tpnb': tpnbList[0],
    #'tpnc': '{string}',
    #'catid': '{string}',
})
ind = 0
itemPages = range(pages)
itemPages = [i*limit for i in itemPages]#create list of item number on each page
print len(tpnbList), 'TPNB numbers searched.'
params = ''
for n in range(limit):
    params = params + '&tpnb='+str(tpnbList[n])
try:
    conn = httplib.HTTPSConnection('dev.tescolabs.com')
    conn.request("GET", "/product/?%s" % params, "{body}", headers)
    response = conn.getresponse()
    prodData = response.read()
    PRODDATA = json.loads(prodData)
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))

for i in range(len(tpnbList)):
    if i in itemPages[1:]: #for each i in the page list
        params = ''
        for n in range(limit):
            params = params + '&tpnb='+str(tpnbList[itemPages[ind]+n])
        print params
        try:
            conn = httplib.HTTPSConnection('dev.tescolabs.com')
            conn.request("GET", "/product/?%s" % params, "{body}", headers)
            response = conn.getresponse()
            prodData = response.read()
            NEWPRODDATA = json.loads(prodData)
            PRODDATA['products'].extend(NEWPRODDATA['products'])
            conn.close()
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
        ind += 1

print len(PRODDATA['products']), 'products data found.' #length seems wrong maybe multiple results for 1 tpnb?
checkList = []
for element in PRODDATA['products']:
    if element['description'] not in checkList:
        checkList.append(element['description'])
print len(checkList)

# Create list of food items
print len(PRODDATA['products']), 'items from search.'
foodList = []
for element in PRODDATA['products']:
    if element['productCharacteristics']['isFood'] == True:
        foodList.append(element)
print len(foodList), 'of which are food.'
# Remove items without nutrition data
nutriList = []
for element in foodList:
    #print element.keys()
    if 'calcNutrition' in element.keys():
        if 'calcNutrients' in element['calcNutrition'].keys():
            nutriList.append(element)
print len(nutriList), 'of which have nutritional information'
# Remove items without quantity data
qtyList = []
for element in nutriList:
    #print element.keys()
    if 'qtyContents' in element.keys():
        qtyList.append(element)
print len(qtyList)
# Remove items without gram weights
gramList = []
for element in qtyList:
    #print element.keys()
    #try:
    if ('quantityUom' in element['qtyContents'] and
        element['qtyContents']['quantityUom'] == 'g'):
        gramList.append(element)
    elif 'quantity' in element['qtyContents'].keys():
            #print 'yes'
        element['qtyContents']['quantityUom'] = 1000*element['qtyContents']['quantity']
        gramList.append(element)
    #except:
       # print element['name']
#print qtyList[0]

count = 0
for element in nutriList:
    if element not in gramList:
        element['qtyContents'] = {}
        count = count + 1
        for i in DATA['uk']['ghs']['products']['results']:
            if int(element['tpnb']) == i['tpnb']: #annoyingly search data returns tbnp as int but product data is str
                #print i
                element['qtyContents']['quantity'] = 10*i['AverageSellingUnitWeight']
                #count = count + 1
print count, 'items quantity data inferred.'

#Normalise weight units to grams
#for i in gramList[:10]:
 #   print i['qtyContents']
#print gramList[0].keys()
count = 0
for element in nutriList:
    for i in DATA['uk']['ghs']['products']['results']:
        if int(element['tpnb']) == i['tpnb']: #annoyingly search data returns tbnp as int but product data is str
            element['price'] = i['price']
            element['name'] = i['name']
            count += 1
            #print element['name'], i['name']
#print DATA['uk']['ghs']['products']['results'][0]['price']
print count, 'items matched.'
for i in gramList[:9]:
    print i['price']
    
    # For a start let's try to calculate protein grams per kcal and per £
info = []
itemCount = 0
noProtein = 0
#print len(DATA['uk']['ghs']['products']['results'])

for n in nutriList:
    try:
        #print n['calcNutrition']['calcNutrients']
        for element in n['calcNutrition']['calcNutrients']:
            #print element
            for k, v in element.items():
                #print v
                if v == 'Protein (g)':
                    #print n['name']
                #print element['valuePer100']
                    n['proteinPer100 (g)'] = element['valuePer100']

                elif v == 'Energy (kcal)':
                    #print element['valuePer100']
                    n['kcalPer100'] = element['valuePer100']
        n['proteinPerGBP'] = (float(n['proteinPer100 (g)'])*
                                   0.01*float(n['qtyContents']['quantity'])/float(n['price']))
        n['proteinPerKcal'] = (float(n['proteinPer100 (g)'])/
                                       float(n['kcalPer100']))
        itemCount += 1
    except:
        noProtein += 1
print itemCount, noProtein #nutriList[0]['proteinPer100 (g)']

#Clean up data
cleanInfo = []
nameList = []
dupeCount = 0
for element in nutriList:
    #print element
    if element['name'] not in nameList:
        if 'proteinPerKcal' in element.keys():
            element['kcalGBPproduct'] = element['proteinPerKcal']*element['proteinPerGBP']
            cleanInfo.append(element)
            nameList.append(element['name'])
        else:
            print element['name'], 'kcal data absent'
    else:
        dupeCount += 1
        #print element['name'], 'duplicate found'
#print 'British Chicken Breast Portions 650G' not in nameList, 'unique products evaluated'
#print nameList[-9:]
print dupeCount
        
#Limit data to 30 results
cleanInfoSrt = sorted(cleanInfo, key = lambda i: i['proteinPerKcal'], reverse=True)
cleanInfoSrtGBP = sorted(cleanInfo, key = lambda i: i['proteinPerGBP'], reverse=True)
cleanInfoSrtProd = sorted(cleanInfo, key = lambda i: i['kcalGBPproduct'], reverse=True) 
cleanInfoSrt = cleanInfoSrt[0:10]
#for n in cleanInfoSrt:
 #   print n['name'][6:]
cleanInfoSrt.extend(cleanInfoSrtGBP[0:10])
cleanInfoSrt.extend(cleanInfoSrtProd[0:10])
cleanInfo30 = []
for i in range(len(cleanInfoSrt)):
    if cleanInfoSrt[i] not in cleanInfoSrt[i+1:]:
        cleanInfo30.append(cleanInfoSrt[i])
#for n in cleanInfo30:
    #n['name'] = n['name'][6:]
    
    import matplotlib.pyplot as plt
x = []
y = []
lbl = []
for element in cleanInfo30:
    x.append(float(element['proteinPerKcal']))
    y.append(float(element['proteinPerGBP']))
    lbl.append(element['name'])
    
for i,type in enumerate(lbl):
    x_co = x[i]
    y_co = y[i]
    plt.scatter(x_co, y_co, marker='o', color='red')
    plt.text(x_co+0.0, y_co+0.3, type, fontsize=9)

plt.ylabel('Protein per GBP')
plt.xlabel('Protein per kcal')
plt.rcParams["figure.figsize"] = (14,10)
plt.show()
