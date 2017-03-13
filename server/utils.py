# -*- coding: utf-8 -*-

import logging
from PIL import Image
import requests
import pytesseract
from bs4 import BeautifulSoup
import StringIO
from lxml import etree



def get_captcha(type):
    s = requests.Session() 
    if type == 'ruc':
        try:
            r = s.get('http://www.sunat.gob.pe/cl-ti-itmrconsruc/captcha?accion=image')
        except s.exceptions.RequestException as e:
            return (False,e)
        img=Image.open(StringIO.StringIO(r.content))
        captcha_val=pytesseract.image_to_string(img)
        captcha_val=captcha_val.strip().upper()
        return (s, captcha_val)
    elif type == 'dni':
        try:
            r = s.get('https://cel.reniec.gob.pe/valreg/codigo.do')
        except s.exceptions.RequestException as e:
            return (False,e)
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
        

def getValue(type, value):

    res={}
    if value and type == 'dni':
        if len(value)==8:
            for i in range(10):
                consuta, captcha_val= get_captcha(type)
                if not consuta:
                    res['warning'] = {}
                    res['warning']['title'] = _('Connection error')
                    res['warning']['message'] = _('The server is not available! try again!')
                    return res
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
            print "iteration n"
            error_captcha="Ingrese el código que aparece en la imagen"
            error_dni="El DNI N°"
            if error_captcha==name.strip().encode('utf-8'):
                return getValue(type, value)
            elif error_dni==name.strip().encode('utf-8'):
                res['error'] = {}
                res['error']['message'] = _('the DNI entered is incorrect')
                return res
            print "###########"

            res['value'] = {'name':name.strip() or None}
            return res

    elif value and type == 'ruc':
            res={'value':{}}
            factor = '5432765432'
            sum = 0
            dig_check = False
            if len(value) != 11:
                return False
            try:
                int(value)
            except ValueError:
                return False 
                            
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
                res['error'] = {}
                res['error']['message'] = _('the RUC entered is incorrect')
                return res
                
            for i in range(10):
                consuta, captcha_val= get_captcha(type)
                if not consuta:
                    res['warning'] = {}
                    res['warning']['title'] = _('Connection error')
                    res['warning']['message'] = _('The server is not available! try again!')
                    return res
                if captcha_val.isalpha():
                    break
            get=consuta.get("http://www.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias?accion=consPorRuc&razSoc="+
                            "&nroRuc="+value+"&nrodoc=&contexto=rrrrrrr&tQuery=on&search1="+value+
                            "&codigo="+captcha_val+"&tipdoc=1&search2=&coddpto=&codprov=&coddist=&search3=")
            texto_error='Surgieron problemas al procesar la consulta'
            texto_consulta=get.text
            #~ print texto_consulta
            #busqueda_error=texto_consulta.find(texto_error)
            if texto_error in (texto_consulta):
                res['error'] = {}
                res['error']['message'] = _('Consulte nuevamente')
                return res
            else:
                #consulta(ruc)
                texto_consulta=StringIO.StringIO(texto_consulta).readlines()
                
                temp=0;
                tnombre=False
                tdireccion=False
                tncomercial=False
                tstate=False
                tdistrict=False


                        
                for li in texto_consulta:
                    if temp==1:
                        soup = BeautifulSoup(li, "lxml")
                        tdireccion= soup.td.string
                        #~  Extrae distrito sin espacios
                        district = " ".join(tdireccion.split("-")[-1].split()) 
                        #~ Borra distrito, provincia y espacios duplicados
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
                        tactive = soup.td.string
                        #if tactive != 'ACTIVO':
                        #   raise osv.except_osv(
                        #    _('Advertencia'),
                        #    _('El RUC ingresado no esta ACTIVO')) 
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
                            tstate = str(soup.p.string)
                            tstate=tstate[0:6]
                            if tstate == 'HABIDO':
                                tstate = 'habido'
                        else:
                            tstate = 'nhabido'
                        break
                    # linea encontrada
                    if li.find("Condici&oacute;n del Contribuyente:") != -1:
                        temp=1
                        
                res['value'] = {'registration_name':tnombre,
                                'name':tncomercial,
                                'street':tdireccion,
                                'district':tdistrict,
                                'state':tstate,
                                'active':tactive}
                return res

                #self.registration_name = tnombre
                #self.name = tncomercial
                #self.street = tdireccion
                #self.vat_subjected = True
                #self.is_company = True
                #self.state = tstate
    else:
        return False

