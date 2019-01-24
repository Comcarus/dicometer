import pydicom
import numpy as np
from tkinter import messagebox
from base64 import b16encode
import os

def gray2hex(gray):
    return "#{:02x}{:02x}{:02x}".format(gray, gray, gray)


class DicomHandler:
    def __init__(self, master, path, isDir):
        self.master = master
        self.path = path
        self.isDir = isDir

    def parseDirectory(self):
        files = os.listdir(self.path)
        metaArr = []
        imagesArr = []
        for file in files:
            images, meta = self.parseFile(self.path + "/" + file)
            if images and meta:
                imagesArr.append(images)
                metaArr.append(meta)
        return np.array(imagesArr).flatten(), metaArr

    def parseFile(self, path):
        dataset = pydicom.dcmread(path)
        metainfo = {}

        try:
            metainfo['pixelSpacing'] = dataset[0x0028, 0x0030]
            metainfo['imagePosition'] = dataset[0x0020, 0x0032]
            metainfo['imageOrientation'] = dataset[0x0020, 0x0037]
        except:
            return False, False

        pixelArray = dataset.pixel_array
        images = []
        if len(pixelArray.shape) == 2:
            images = [pixelArray]
        else:
            for img in images:
                images.append(pixelArray)

        return images, metainfo

