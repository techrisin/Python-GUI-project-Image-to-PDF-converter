from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window 
from kivy.clock import Clock,mainthread
from kivy.properties import NumericProperty, StringProperty
from kivymd.uix.textfield import MDTextFieldHelperText
from kivymd.uix.label import MDLabel
import re,os, sys, json,time
from kivy.properties import StringProperty, NumericProperty, Property
from kivymd.uix.screen import MDScreen  
import threading
import webbrowser
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.snackbar.snackbar import MDSnackbar,MDSnackbarText
from functools import partial

gwd = os.path.dirname(os.path.realpath(__file__))

sys.path.append(gwd + '/mods')
# sys.path.append(gwd + '/mods/PIL')

print('Importing')
import img2pdf
import PIL.Image as Image
import kivymd

onandroid = 1

infodots = ''

try:
    from android.storage import primary_external_storage_path
except Exception as e:
    print(e)
    v = 1


def getsettings():
    if os.path.isfile(gwd + '/settings/settings.json'):
        with open(gwd + '/settings/settings.json', "r") as read_file:
            data = json.load(read_file)
    else:
        data = {'folder' : '', 'convertall' : False}

    return data 

def setsettings(key,value):
    data = getsettings()
    data[key] = value
    with open(gwd + '/settings/settings.json', 'w') as gp:
        json.dump(data, gp, indent=4)


def checkimage(path):
    isimage = False
    formats = ['png','jpg','tif','gif']
    for format in formats:
        if path.endswith('.' + format) :
            try:
                img = Image.open(path)
                isimage = True
                print(path +  ' is image')
            except IOError:
                v = 1
    return isimage


def processImages(self,path,dir=False, *largs):
    filepath = path
    if dir:
        if os.path.isdir(filepath):
            imgs = []
            for fname in os.listdir(filepath):
                
                if not checkimage(os.path.join(filepath, fname)):
                    continue
                path = os.path.join(filepath, fname)
                if os.path.isdir(path):
                    continue
                self.ids.infotext.text = "Adding " + os.path.split(path)[1]
                imgs.append(path)
            if len(imgs) > 0:
                savepdf(self,imgs,filepath,3)
                print('Processed images in folder ' + path)
                
                setsettings('folder', filepath)
            else:
                app.opensnackbar('No images in folder')

    else : # if os.path.isfile(filepath):
        if str(self.ids.cb.state) == 'down':
            processImages(self,os.path.split(filepath[0])[0],True)
            
            
        else:
            imgs = []
            for fname in path:
                
                if not checkimage(fname):
                    continue
                # path = os.path.join(filepath, fname)
                if os.path.isdir(fname):
                    continue
                imgs.append(fname)
            if len(imgs) > 0:
                print(filepath[0])
                setsettings('folder', os.path.split(filepath[0])[0])
                
                if len(imgs) > 1:
                    savepdf(self,imgs,os.path.split(filepath[0])[0],2)
                    
                else:
                    savepdf(self,imgs,os.path.split(filepath[0])[0],1)

def dynamictext(self,dt):
    global infodots
    infodots += '.'
    if infodots == '....':
        infodots = ''
    self.ids.infotext.text = 'Converting' + infodots
    print(infodots)

def startdynamictext(self,dt):
    self.intervalfn = Clock.schedule_interval(partial(dynamictext,self),dt)


def write(self,dest,imgs,msgtype):
    print('v from write fn')
    with open(dest + "/output-" + time.strftime("%Y%m%d-%H%M%S") + ".pdf", "wb") as f:
        f.write(img2pdf.convert(imgs))
        print('Processed images')
    self.intervalfn.cancel()
    self.ids.infotext.text = ''
    self.pdfgenerated = True
    self.msgtype = msgtype

# class MainScreen(MDScreen):
#     pass
# class InfoScreen(MDScreen):
#     pass

def savepdf(self,imgs,dest,msgtype):
    if onandroid:
        tocheck = ['document', 'download','picture','movie','recording','dcim']
        writeaccess = False 
        externalfolders = os.listdir(self.storage_path)
        destfolder = 'ToGetFolderName'

        
        for folder in tocheck:
            for extfolder in externalfolders:
                if not writeaccess:
                    if folder in extfolder.lower() and os.access(self.storage_path + '/' + extfolder, os.W_OK):
                        writeaccess = True
                        destfolder = extfolder
        if destfolder == 'ToGetFolderName':
            if os.access(self.storage_path , os.W_OK):
                destfolder = ''

        if not destfolder == 'ToGetFolderName':
            # dest = self.storage_path + '/Documents/Image to PDF by Techris'
            self.destFolder = destfolder
            try : 
                os.mkdir(self.storage_path  + '/' + destfolder + '/Image to PDF by Techris')
            except Exception as e:
                print(e)
        
            self.pdfgenerated = False
            app.checkpdfstatus(0.25)
            # t1 = threading.Thread(target=self.checkpdfstatus, args=(msgtype,))
            t2 = threading.Thread(target=startdynamictext, args=(self,0.5,))
            t3 = threading.Thread(target=write, args=(self,self.storage_path  + '/' + destfolder + '/Image to PDF by Techris',imgs,msgtype))
            
            # t1.start()
            t2.start()
            t3.start()
        else:
            app.opensnackbar('PDF cant be saved due\nto write permission issue')

    else:
        self.pdfgenerated = False
        app.checkpdfstatus(0.25)
        # t1 = threading.Thread(target=self.checkpdfstatus, args=(msgtype,))
        t2 = threading.Thread(target=startdynamictext, args=(self,0.5,))
        t3 = threading.Thread(target=write, args=(self,dest,imgs,msgtype))
        
        # t1.start()
        t2.start()
        t3.start()
        
class techrisApp(MDApp):
    
    def build(self):
        # Window.size = [300, 500]
        self.theme_cls.primary_palette = "Turquoise"
        # vb = Builder.load_file('assets/kv/gui.kv')
        if onandroid:
            vb = Builder.load_file('assets/kv/gui-android.kv')
        else:
            vb = Builder.load_file('assets/kv/gui.kv')
        if onandroid:
            self.storage_path = primary_external_storage_path()
        else:
            self.storage_path = gwd # os.path.expanduser("~")  # path to the directory that will be opened in the file manager
        
        
        
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,  # function called when the user reaches directory tree root
            select_path=self.select_path,  # function called when selecting a file/directory
            # preview = True,
            selector='multi'
        )
        
        return vb
    
    
    # @mainthread
    def checkpdfstatus(self,dt):

        if self.pdfgenerated :
            if self.msgtype == 1 :
                if onandroid:
                    app.opensnackbar('Processed One image\n\nPDF saved in ' + self.destFolder + '/Image to PDF by Techris folder')
                else:
                    app.opensnackbar('Processed One image\n\nPDF saved in same folder')

            elif self.msgtype == 2:
                if onandroid:
                    app.opensnackbar('Processed images\n\nPDF saved in ' + self.destFolder + '/Image to PDF by Techris folder')
                else:
                    app.opensnackbar('Processed images\n\nPDF saved in same folder')
            elif self.msgtype == 3 :
                if onandroid:
                    app.opensnackbar('Processed all images in folder\n\nPDF saved in ' + self.destFolder + '/Image to PDF by Techris folder')
                else:
                    app.opensnackbar('Processed all images in folder\n\nPDF saved in same folder')
        else:
            Clock.schedule_once(self.checkpdfstatus,0.25)
    
    
    
    def opensnackbar(self,text):
        MDSnackbar(
                MDSnackbarText(
                    text=text,
                ),
                y="24dp",
                pos_hint={"center_x": 0.5},
                size_hint_x=0.9,
                duration=6
            ).open()
    
    def on_start(self):
        super().on_start()
        v = 1
        self.ids = self.root.screens[0].ids
        data = getsettings()
        self.ids.cb.active = data['convertall'] 
        
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.READ_MEDIA_IMAGES, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
        except Exception as e:
            print(e)
            v = 1
        # self.root
    def visitmsm(self):
        webbrowser.open('https://techris.in/contact-us/') 

    def openfile(self):
        data = getsettings()
        if not data['folder'] == '':
            if os.path.isdir(data['folder']):
                # self.storage_path = data['folder']
                self.file_manager.show(data['folder'])
            else:
                self.file_manager.show(self.storage_path)

    def exit_manager(self, *args):
        self.manager_open = False
        self.file_manager.close()

    def select_path(self,path):
        # print(path)
        setsettings('convertall', str(self.ids.cb.state) == 'down')
        # print(self.file_manager.selection)
        self.exit_manager()
        Clock.schedule_once(partial(processImages,self,self.file_manager.selection,0),1)
        
        
    
    def showinfo(self):
        self.root.current='info'
    def showcredits(self):
        self.root.current='credits'
    
    def showmainscreen(self):
        self.root.current='main'
app = techrisApp()
app.run()