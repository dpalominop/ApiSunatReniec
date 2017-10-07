# -*- coding: utf-8 -*-

import logging
from PIL import Image
import requests
import pytesseract
from bs4 import BeautifulSoup
import StringIO
from lxml import etree


def httpGet(session, url, timeout=6.05):
    error = {'title':'Connection error','message':'', 'log':None}

    try:
        req = session.get(url, timeout=timeout)
    except requests.exceptions.Timeout as e:
        error['message'] = 'The request timed out while trying to connect to the remote server. Or The server did not send any data in the allotted amount of time.'
        error['log'] = str(e)
        return error

    except requests.exceptions.HTTPError as e:
        error['message'] = 'An HTTP error occurred.'
        error['log'] = str(e)
        return error

    except requests.exceptions.RequestException as e:
        error['message'] = 'There was an ambiguous exception that occurred while handling your request.'
        error['log'] = str(e)
        return error

    texto_error = "La página que Ud. desea consultar no existe o en éste momento no se encuentra disponible"
    if texto_error in (req.text.encode('utf-8')):
        error['message'] = 'La página que Ud. desea consultar no existe o en éste momento no se encuentra disponible.'
        error['title'] = 'Server Error'
        return error

    texto_error='Surgieron problemas al procesar la consulta'
    texto_consulta=req.text
    if texto_error in (texto_consulta):
        error['title'] = 'Server Error'
        error['message'] = 'Consulte nuevamente'
        return error

    return req

def get_captcha(docType):
    s = requests.Session()
    if docType == 'ruc':

        r = httpGet(s, 'http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/captcha?accion=image')
        if type(r) is dict:
            return (False, r)

        img=Image.open(StringIO.StringIO(r.content))
        captcha_val=pytesseract.image_to_string(img)
        captcha_val=captcha_val.strip().upper()
        return (s, captcha_val)

    elif docType == 'dni':

        r = httpGet(s, 'https://cel.reniec.gob.pe/valreg/codigo.do')
        if type(r) is dict:
            return (False, r)

        img=Image.open(StringIO.StringIO(r.content))
        img = img.convert("RGBA")
        pixdata = img.load()
        for y in xrange(img.size[1]):
            for x in xrange(img.size[0]):
                red, green, blue, alpha=pixdata[x, y]
                if blue<100:
                    pixdata[x, y] = (255, 255, 255, 255)
        temp_captcha_val=pytesseract.image_to_string(img)
        temp_captcha_val=temp_captcha_val.strip().upper()
        captcha_val=''
        for i in range(len(temp_captcha_val)):
            if temp_captcha_val[i].isalpha() or temp_captcha_val[i].isdigit():
                captcha_val=captcha_val+temp_captcha_val[i]
        return (s, captcha_val.upper())


def getValue(docType, value):

    res = {}
    if value and docType == 'dni':
        if len(value)==8:
            for i in range(10):
                consuta, captcha_val= get_captcha(docType)
                if not consuta:
                    return {'error': captcha_val}

                if len(captcha_val)==4:
                    break

            payload={'accion': 'buscar', 'nuDni': value, 'imagen': captcha_val}
            post = consuta.post("https://cel.reniec.gob.pe/valreg/valreg.do", params=payload)
            texto_consulta=post.text
            parser = etree.HTMLParser()
            tree   = etree.parse(StringIO.StringIO(texto_consulta), parser)
            res= {}
            name=''
            for _td in tree.findall("//td[@class='style2']"):
                if _td.text:
                    _name=_td.text.split("\n")
                    for i in range(len(_name)):
                        _name[i]=_name[i].strip()
                    name=' '.join(_name)
                    break

            error_captcha="Ingrese el código que aparece en la imagen"
            error_dni="El DNI N°"
            if error_captcha==name.strip().encode('utf-8'):
                return getValue(docType, value)
            elif error_dni==name.strip().encode('utf-8'):
                return {'error': {'title':'User error', 'message': 'the DNI entered is incorrect', 'log': None}}

            res = {'name':name.strip() or None}
            return res
        else:
            return {'error': {'title':'User error', 'message': 'the DNI entered is incorrect', 'log': None}}

    elif value and docType == 'ruc':

        res = {}
        factor = '5432765432'
        sum = 0
        dig_check = False
        if len(value) != 11:
            return {"error": {'title':'User error', 'message': 'the RUC entered is incorrect', 'log': None}}
        try:
            int(value)
        except ValueError:
            return {"error": {'title':'User error', 'message': 'the RUC entered is incorrect', 'log': None}}

        for f in range(0,10):
            sum += int(factor[f]) * int(value[f])

        subtraction = 11 - (sum % 11)
        if subtraction == 10:
            dig_check = 0
        elif subtraction == 11:
            dig_check = 1
        else:
            dig_check = subtraction

        if not int(value[10]) == dig_check:
            return {'error': {'title':'User error', 'message': 'the RUC entered is incorrect', 'log': None}}

        for i in range(10):
            consuta, captcha_val= get_captcha(docType)
            if not consuta:
                return {'error': captcha_val}

            if captcha_val.isalpha():
                break

        get = httpGet(consuta, "http://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorRuc&razSoc="+
                        "&nroRuc="+value+"&nrodoc=&contexto=rrrrrrr&tQuery=on&search1="+value+
                        "&codigo="+captcha_val+"&tipdoc=1&search2=&coddpto=&codprov=&coddist=&search3=")

        if type(get) is dict:
            return {'error': get}
        else:
            #consulta(ruc)
            texto_consulta=StringIO.StringIO(get.text).readlines()

            temp=0;
            tnombre=False
            tdireccion=False
            tncomercial=False
            condition=False
            tdistrict=False
            tstate=False



            for li in texto_consulta:
                if temp==1:
                    soup = BeautifulSoup(li, "lxml")
                    tdireccion= soup.td.string
                    #~  Extrae distrito sin espacios
                    district = " ".join(tdireccion.split("-")[-1].split())
                    #~ Borra distrito, provincia y espacios duplicados
                    tprovince = " ".join(tdireccion.split("-")[-2].split())
                    tdireccion = " ".join(tdireccion.split())
                    tdireccion = " ".join(tdireccion.split("-")[0:-2])

                    #~ Busca el distrito
                    #ditrict_obj = self.env['res.country.state']
                    #dist_id = ditrict_obj.search([('name', '=', district),('province_id', '!=', False),('state_id', '!=', False)], limit=1)
                    #if dist_id:
                    #    self.district_id = dist_id.id
                    #    self.province_id = dist_id.province_id.id
                    #    self.state_id = dist_id.state_id.id
                    #    self.country_id = dist_id.country_id.id
                    #    logging.getLogger('server2').info('res:%s'%(res))

                    tdistrict = district
                    break

                if li.find("Domicilio Fiscal:") != -1:
                    temp=1

            #print texto_consulta
            for li in texto_consulta:
                if li.find("desRuc") != -1:
                    soup = BeautifulSoup(li, "lxml")
                    tnombre=soup.input['value']

                    break

            # Nombre comercial
            temp=0;
            for li in texto_consulta:
                if temp==1:
                    soup = BeautifulSoup(li, "lxml")
                    tncomercial = soup.td.string
                    if tncomercial == "-":
                        tncomercial = tnombre
                    break

                if li.find("Nombre Comercial:") != -1:
                    temp=1

            # Estado ACTIVO
            temp=0;
            for li in texto_consulta:
                if temp==1:
                    soup = BeautifulSoup(li, "lxml")
                    tstate = soup.td.string
                    #if tstate != 'ACTIVO':
                    #   raise osv.except_osv(
                    #    ('Advertencia'),
                    #    ('El RUC ingresado no esta ACTIVO'))
                    break

                if li.find("Estado del Contribuyente:") != -1:
                    temp=1

            # Estado Habido / No habido
            temp=0;
            for li in texto_consulta:

                # El resultado se encuentra 3 lineas por debajo de la linea encontrada
                if temp>=1:
                    temp += 1
                if temp==4:
                    soup = BeautifulSoup(li, "lxml")
                    # Si contiene la etiqueta "p" es HABIDO, caso contrario es un link <a> de NO HABIDO
                    if soup.p:
                        condition = str(soup.p.string)
                        condition=condition[0:6]
                        if condition == 'HABIDO':
                            condition = 'HABIDO'
                    else:
                        condition = 'NO HABIDO'
                    break
                # linea encontrada
                if li.find("Condici&oacute;n del Contribuyente:") != -1:
                    temp=1

            res = {'legal_name':tnombre,
                    'commercial_name':tncomercial,
                    'street':tdireccion,
                    'district':tdistrict,
                    'province':tprovince,
                    'condition':condition,
                    'state':tstate}
            return res

            #self.registration_name = tnombre
            #self.name = tncomercial
            #self.street = tdireccion
            #self.vat_subjected = True
            #self.is_company = True
            #self.state = condition
    else:
        return {'error': {'title':'User error', 'message': 'Parameters required!', 'log': None}}
