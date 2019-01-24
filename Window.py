from tkinter import Frame, Menu, Canvas, filedialog, messagebox
from PIL import Image, ImageTk
from DicomHandler import DicomHandler
import numpy as np
from sys import platform as sys_pf

# OSX build fix
if sys_pf == 'darwin':
    import matplotlib
    matplotlib.use("TkAgg")

import json
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from voxelMethods import getVoxelPosition

POINT_RADIUS_HALF = 3


class Window(Frame):

    def __init__(self, root, size=(500, 500)):
        super().__init__()
        self.root = root
        self.size = size
        self.root.geometry(str(self.size[0]) + "x" + str(self.size[1]) + "+0+0")
        self.dicomHandler = None
        self.canvas = None

        self.imageShown = False
        self.imagesToShow = []
        self.imagesSlideshow = False
        self.imagesMeta = []
        self.imageCount = 0

        self.points = []
        self.pointsForImages = []
        self.initUI()

    def initUI(self):
        self.master.title("Dicometer")
        self.menubar = Menu(self.master)
        self.master.config(menu=self.menubar)
        fileMenu = Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=fileMenu)
        fileMenu.add_command(label="Open single file", command=self.onFileOpen)
        fileMenu.add_command(label="Open directory", command=self.onDirOpen)
        fileMenu.add_command(label="Exit", command=self.onExit)

        slideshowControlls = Menu(self.menubar)
        self.menubar.add_cascade(label="Controlls", menu=slideshowControlls)
        slideshowControlls.add_command(label="Next", command=self.onNextImage)
        slideshowControlls.add_command(label="Preview", command=self.onPreview)
        slideshowControlls.add_command(label="View Metrics", command=self.onMetrics)
        slideshowControlls.add_command(label="Export", command=self.onExport)

        helpControlls = Menu(self.menubar)
        self.menubar.add_cascade(label="Help", menu=helpControlls)
        helpControlls.add_command(label="Reference", command=self.onReference)

        self.menubar.entryconfig("Controlls", state="disabled")
        self.initCanvas(self.size)
        self.canvas.create_text(
            self.size[0] >> 1,
            self.size[1] >> 1,
            text="Open file or directory by following File option",
            fill="black"
        )

    def initCanvas(self, size):
        if self.canvas:
            self.canvas.destroy()
        self.canvas = Canvas(self.root, width=size[0], height=size[1])
        self.canvas.pack(expand=1)
        self.canvas.bind("<Button-1>", self.onMouseClicked)
        self.canvas.bind("<Button-2>", self.onMouseRightClicked)

    def showImage(self, imageToShow):
        width, height = np.array(imageToShow).shape
        self.root.geometry(str(width) + "x" + str(height))
        self.initCanvas((width, height))

        img = ImageTk.PhotoImage(image=Image.fromarray(imageToShow))
        self.root.img = img
        self.canvas.create_image((0, 0), image=img, state="normal", anchor="nw")
        self.imageShown = True

    def redraw(self):
        self.showImage(self.imagesToShow[self.imageCount])
        self.drawDynamic()

    def getPointsForImages(self, images):
        print("Requesting points for images")
        self.imagesToShow = images
        self.imagesSlideshow = True
        self.showImage(images[0])
        self.showSlideshowMenu()

    def showSlideshowMenu(self):
        self.menubar.entryconfig("Controlls", state="normal")

    def drawDynamic(self):
        for point in self.points:
            self.canvas.create_oval(
                point[0] - POINT_RADIUS_HALF,
                point[1] - POINT_RADIUS_HALF,
                point[0] + POINT_RADIUS_HALF,
                point[1] + POINT_RADIUS_HALF,
                fill="#ff0000",
                outline="#ff0000"
            )

    def onExit(self):
        self.quit()

    def onFileOpen(self):
        path = filedialog.askopenfilename()
        if path is None:
            return
        self.dicomHandler = DicomHandler(self, path, False)
        images, meta = self.dicomHandler.parseFile(self.dicomHandler.path)
        self.imagesMeta = [meta]
        self.getPointsForImages(images)

    def onDirOpen(self):
        path = filedialog.askdirectory()
        if path is None:
            return
        self.dicomHandler = DicomHandler(self, path, True)
        images, meta = self.dicomHandler.parseDirectory()
        self.imagesMeta = meta
        self.getPointsForImages(images)

    def onMouseClicked(self, event):
        if self.imageShown:
            point = (event.x, event.y)
            self.points.append(point)
        self.redraw()

    def onMouseRightClicked(self, event):
        if self.imageShown and len(self.points) != 0:
            point = (event.x, event.y)
            self.points = [x for x in self.points if abs(x[0] - point[0]) > 3 and abs(x[1] - point[1]) > 3]
        self.redraw()

    def onNextImage(self):
        self.pointsForImages.append(self.points)
        self.imageCount += 1
        self.points = []
        if len(self.imagesToShow) > self.imageCount:
            self.showImage(self.imagesToShow[self.imageCount])
        else:
            messagebox.showinfo("No more images were opened", "You have pointed all images, export or preview now")

    def getAllPoints(self):
        return self.pointsForImages + [self.points]

    def getXYZPoints(self):
        X = []
        Y = []
        Z = []
        for imageIndex, pointsForImage in enumerate(self.getAllPoints()):
            for point in pointsForImage:
                meta = self.imagesMeta[imageIndex]
                x, y, z = getVoxelPosition(point, meta["pixelSpacing"], meta["imagePosition"], meta["imageOrientation"])
                X.append(x)
                Y.append(y)
                Z.append(z)
        return X, Y, Z

    def onPreview(self):
        X, Y, Z = self.getXYZPoints()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(X, Y, Z)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.show()

    def getMetrics(self):
        X, Y, Z = self.getXYZPoints()
        xMax, xMin = np.amax(X), np.amin(X)
        yMax, yMin = np.amax(Y), np.amin(Y)
        zMax, zMin = np.amax(Z), np.amin(Z)
        return abs(xMax - xMin), abs(yMax - yMin), abs(zMax - zMin)

    def onMetrics(self):
        x, y, z = self.getMetrics()
        messagebox.showinfo("Metrix",   "X metrix is " + str(x) + "mm \n"
                                        "Y metrix is " + str(y) + "mm \n"
                                        "Z metrix is " + str(z) + "mm \n"
        )

    def onExport(self):
        includeMetrics = messagebox.askyesno("Export", "Would tou like to include metrics?")
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path is None:
            return

        x, y, z = self.getXYZPoints()
        data = {
            "points": {}
        }
        data["points"]["x"] = x
        data["points"]["y"] = y
        data["points"]["z"] = z

        if includeMetrics:
            x, y, z = self.getMetrics()
            data["metrics"] = {}
            data["metrics"]["x"] = x
            data["metrics"]["y"] = y
            data["metrics"]["z"] = z
            data["metrics"]["units"] = "mm"

        with open(path, 'w') as outfile:
            json.dump(data, outfile)

        messagebox.showinfo("Exported", "Operation is successful you can obtain your file at '" + path + "'")


    def onReference(self):
        messagebox.showinfo("Reference", "Menu: \n"
                                         "Controlls -> Next: next picture in sequence \n"
                                         "Controlls -> Export: Exports points data in .json format \n"
                                         "Image proccessing: \n"
                                         "To create point: left mouse click on canvas\n"
                                         "To remove point: right mouse click on canvas near the corresponding point\n"
        )
