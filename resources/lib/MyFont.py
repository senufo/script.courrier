# script constantes
__script__       = "MyFont.py"
__author__       = "Ppic, Frost"
__credits__      = "Team XBMC-Passion, http://passion-xbmc.org/"
__platform__     = "xbmc media center, [LINUX, OS X, WIN32, XBOX]"
__date__         = "29-12-2009"
__version__      = "1.0"

#python librairy to add font to the current skin. need to have font_filename.ttf in /resources/fonts/, this script will automatically add it to current skin when called.

import os
import elementtree.ElementTree as ET
import shutil
from traceback import print_exc
import xbmc


skin_font_path = xbmc.translatePath("special://skin/fonts/")
script_font_path = os.path.join(os.getcwd() , "resources" , "fonts")
skin_dir = xbmc.translatePath("special://skin/")
list_dir = os.listdir( skin_dir )

print skin_font_path
print script_font_path


def addfont( fontname , filename , size , style="", aspect="" ):
    try:
        reload_skin = False
        fontxml_paths = []
        for item in list_dir:
            item = os.path.join( skin_dir, item )
            if os.path.isdir( item ):
                font_xml = os.path.join( item, "font.xml" )
                if os.path.exists( font_xml ):
                    fontxml_paths.append( font_xml )

        if fontxml_paths:
            for fontxml_path in fontxml_paths:
                print "analyse du fichier: " + fontxml_path
                tree = ET.parse(fontxml_path)
                root = tree.getroot()
                if not isfontinstalled( fontxml_path, fontname ):
                    print "modification du fichier: " + fontxml_path
                    reload_skin = True
                    for sets in root.getchildren():
                        new = ET.SubElement(sets, "font")
                        subnew1=ET.SubElement(new ,"name")
                        subnew1.text = fontname
                        subnew2=ET.SubElement(new ,"filename")
                        subnew2.text = filename
                        subnew3=ET.SubElement(new ,"size")
                        subnew3.text = size
                        if style in [ "normal", "bold", "italics", "bolditalics" ]:
                            subnew4=ET.SubElement(new ,"style")
                            subnew4.text = style
                        if aspect:    
                            subnew5=ET.SubElement(new ,"aspect")
                            subnew5.text = aspect
                    tree.write(fontxml_path)                                        
        
        if not os.path.exists( os.path.join( skin_font_path , filename ) ):
            shutil.copyfile( os.path.join( script_font_path , filename ) , os.path.join( skin_font_path , filename ))
        if reload_skin: xbmc.executebuiltin( "XBMC.ReloadSkin()" )
        
        return(True)
    except:
        print_exc()
        return(False)
    
def isfontinstalled( fontxml_path, fontname ):
    name = "<name>%s</name>" % fontname
    if not name in file( fontxml_path, "r" ).read():
        print "font name not installed!", fontname
        return False
    else:
        print "ok installe font name", fontname
        return True

print "update font: %s" % addfont( "sportlive13" , "sportlive.ttf" , "20" )
print "update font: %s" % addfont( "sportlive24" , "sportlive.ttf" , "24" )
print "update font: %s" % addfont( "sportlive45" , "sportlive.ttf" , "45" )
