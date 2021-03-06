#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 25 20:28:55 2016
The collection of the useful methods used in the TDAP results analysis
"""
__author__ = "Chao Lian <charleslian@126.com>"
__date__ = "Fri July 22 18:16:20 2016"

__version__ = "2.0"
__credits__ = "Chao Lian initial and maintain the codes"

import numpy as np
import os
from pyramids.io.fdf import tdapOptions

def getElectronStepLength(filename='input.in'):
  for line in open(filename).readlines():
      if 'edt' in line.split():
          return float(line.split()[-1].replace(',',''))*0.04838

def read_espresso_out(fileobj='result'):
  from ase.atoms import Atoms, Atom
  from ase import units
  from ase.calculators.singlepoint import SinglePointCalculator
  
  """Reads quantum espresso output text files."""
  if isinstance(fileobj, basestring):
      fileobj = open(fileobj, 'rU')
  lines = fileobj.readlines()
  #print lines
  images = []
  
  for number, line in enumerate(lines):
    if 'number of atoms/cell' in line:
      numAtom = int(line.split()[-1])
    if 'number of atomic types' in line:
      numElement = int(line.split()[-1])
    
    if "atomic species   valence    mass" in line:
      elementLines = lines[number+1:number+1+numElement]
      elementsInfo = [[(i) for i in l.split()] for l in elementLines]
      #print line
    
    

      #print numAtom
    if 'lattice parameter (alat)' in line:
      line = line.strip().split('=')[1].strip().split()[0]
      lattice_parameter = float(line) * units.Bohr
    
    if "crystal axes: (cart. coord. in units of alat)" in line:
      ca_line_no = number
      cell = np.zeros((3, 3))
      for number, line in enumerate(lines[ca_line_no + 1: ca_line_no + 4]):
          line = line.split('=')[1].strip()[1:-1]
          values = [float(value) for value in line.split()]
          cell[number, 0] = values[0]
          cell[number, 1] = values[1]
          cell[number, 2] = values[2]
      cell *= lattice_parameter
    if "site n.     atom                  positions (alat units)" in line:
      initPositionLines = lines[number+1:number+1+numAtom]
      elements = np.array([l.split()[1] for l in initPositionLines])
      scaledPositions = np.array([[float(i) for i in l.split()[6:9]] 
                            for l in initPositionLines])
      #print elements, scaledPositions
      atom = Atoms(symbols=elements, scaled_positions=scaledPositions, cell=cell, pbc=True)
      #print atom
      images.append(atom)                       
           
                   
    cellkey = 'CELL_PARAMETERS (angstrom)'
    posikey = 'ATOMIC_POSITIONS (angstrom)' 
    if posikey in line:
      #print number
#      cellLines = lines[number+1:number+4]
#      cell = np.array([[float(i) for i in l.split()] 
#                        for l in cellLines])
      #print cell
      
      positionLines = lines[number+1:number+1+numAtom]
      elements = np.array([l.split()[0]
                        for l in positionLines])
      #print elements
      
      positions = np.array([[float(i) for i in l.split()[1:]] 
                        for l in positionLines])

      atom = Atoms(symbols=elements, positions=positions, cell=cell, pbc=True)
      images.append(atom)
      
    if "Forces acting on atoms (cartesian axes, Ry/au):" in line:
      #print number
      atom = images[-1]
      forceLines = lines[number+2:number+2+numAtom]
      forces = np.array([[float(i) for i in l.split()[-3:]] 
                        for l in forceLines])
      forces *= units.Ry / units.Bohr
      calc = SinglePointCalculator(atom, forces=forces)
      atom.set_calculator(calc)
  return elementsInfo, images[1:-1]

def readData(filename='pwscf.phase.dat'):
  f = open(filename)
  text = f.readlines()
  nbnd, nkstot = [int(i) for i in text[0].split()]
  kweight = [float(i) for i in text[1].split()]
  
  nstep = (len(text) - 2)/(nkstot+1)
  del text[1]
  del text[::(nkstot+1)]
  data = np.array([[float(i) for i in line.split()] for line in text])
  data = data[:nstep*nkstot].reshape([nstep, nkstot, nbnd])
  return data, np.array(kweight)


def getEELS(filename='q_list',prefix='EELS_'):
  Q = np.loadtxt(filename)
  #print(Q)
  Z = []
  for i, q in enumerate(Q):
    filename = prefix + str(i+1) 
    d = np.loadtxt(filename, delimiter=',')
    E = d[:, 0]
    C = d[:, 2]
    Z.append(C)
  # to plot contour, transpose Z is needed (exchange x and y)
  contour = np.transpose(np.array(Z))
  X, Y = np.meshgrid(Q, E)
  
  return Q, E, X, Y, contour 

#------------------------------------------------------------------------------
def getTime():
  context = open('siesta.times','r').readlines()
  labels = ['Calls', 'Prg.com', 'Prg.com/Tot.com', 'Prg.tot', 'Prg.tot/Tot.tot', 'Nod.avg/Nod.max']
  #print labels

  data = [[float(num) for num in line.split()[1:]] for line in context[13:-13]]
  index = [line.split()[0] for line in context[13:-13]]
  #print index
  #print data
  import pandas as pd
  return pd.DataFrame(data = data, index = index, columns = labels)
#------------------------------------------------------------------------------

def getStructrue():
  if os.path.exists('structure.vasp'):
    from ase.io import read
    atoms = read('structure.vasp',format='vasp')
    #import ase.build
    #ase.build.niggli_reduce(atoms)
  elif os.path.exists('siesta.XV'):
    from ase.calculators.siesta.import_functions import xv_to_atoms
    atoms = xv_to_atoms('siesta.XV')
  return atoms

def pythonGrep(string,filename):
 import re
 return [line for line in open(filename, "r") if re.search(string, line)]

def recoverAllKPoints(kcoor, reciprocal_vectors, repeat = [1,1,1], flatten=True):
  #if plane == 'xy': 
  kall = []
  klist = []
  indexKList = np.arange(kcoor.shape[0])
  points = np.array([(reciprocal_vectors[0,:]*i+
                      reciprocal_vectors[1,:]*j+
                      reciprocal_vectors[2,:]*k) 
                      for i in range(-repeat[0],repeat[0]+1) 
                      for j in range(-repeat[1],repeat[1]+1)
                      for k in range(-repeat[2],repeat[2]+1)])
  for point in points:
    if flatten:  
      kall.extend(kcoor + point)
      kall.extend(-kcoor + point)
      klist.extend(indexKList)
      klist.extend(indexKList)
    else:
      kall.append(kcoor + point)
      kall.append(-kcoor + point)
      klist.append(indexKList)
      klist.append(indexKList)    
  return np.array(kall), np.array(klist)

  
def getImagElectricFunction(direction, dumping=0.00):
  from scipy.fftpack import fft
  timeArray, efield = getEField()  
  timeArray, dipole = getDipolePython()
  
  option = tdapOptions()
  lengthTime = option.tdTimeStep[0]
  
  
  timeArray = timeArray[2:]/option.tdTimeStep[0]
  numStep =  len(timeArray)
  
  dipole = dipole[2:,direction]
  dipole *= np.exp(-dumping*timeArray)
                            
  freqResolution = 1.0/(lengthTime*numStep)
  freqArray = (timeArray-(numStep/2.0))*freqResolution
  
  energyArray = freqArray*4.1356
  energyArray = energyArray[numStep/2:]
  
  epsilon = fft(dipole)[:numStep/2] 
  epsilon = (np.real(epsilon),np.imag(epsilon))
  import pandas as pd
  df = pd.DataFrame({'x-energy':energyArray, 
                    'y1-Im(alpha)':np.abs(epsilon[0]*energyArray/4.1356), 
                    'y2-Re(alpha)':np.abs(epsilon[1]*energyArray/4.1356)})
  #print df
  df.to_csv('DielectricFunction.csv',sep=',')
  return energyArray, np.abs(epsilon[0]*energyArray/4.1356), np.abs(epsilon[1]*energyArray/4.1356)
  
#-------------------------------------------------------------------
def loadSaved(filename):
  filename = filename + '.npy'
  if os.path.exists(filename):
    return np.load(filename)
  else:
    return []
#-------------------------------------------------------------------     
def readBerryFile(step = ''):
  """
  return the Eigenvalues read from systemLabel.EIG
  """
  options = tdapOptions()
  systemLabel = options.label
  BerryFile = open(systemLabel+step+'.Berry')
  Berry = [[float(value) for value in line.split()] for line in BerryFile.readlines()]
  return np.array(Berry)
  
def getBerry():
  options = tdapOptions()
  selectStep = getBerrySteps()
  #print selectStep
  timestep = options.tdTimeStep[0]
  selectTime = selectStep*timestep
  berry = np.array([readBerryFile(str(step)) for step in selectStep])
  return selectTime, berry
#

#-------------------------------------------------------------------  
def getBerrySteps():
  options = tdapOptions()
  stepLines = os.popen('ls '+options.label+'*.Berry').readlines()
  steps = [int(step.split('.')[0].replace(options.label,'')) for step in stepLines]
  return np.sort(steps)
  
def findBandPath(atoms, points, kLine, toleAngle = 0.001):
  reciprocal_vectors = 2*np.pi*atoms.get_reciprocal_cell()
  if os.path.exists('input.fdf'):
    kcoor, kweight = readKpoints()
    kall, klist = recoverAllKPoints(kcoor, reciprocal_vectors)
    #ax.plot(kcoor[:,0], kcoor[:,1],'o')
    #ax.plot(kall[:,0], kall[:,1],'.')
    
  selectedPoints = [(points[name], name) for name in kLine]
  
  lines = [(selectedPoints[i],selectedPoints[i+1]) 
            for i in range(len(selectedPoints) - 1)] 
  kpath = []     
  import pandas as pd
  
  last = 0.0
  xticks = []
  xticks.append(last)
  for a, b in lines:
    coorA = np.dot(a[0],reciprocal_vectors)
    coorB = np.dot(b[0],reciprocal_vectors)
    #ax.plot(coorB[0], coorB[1],'or',ms=20)
    #ax.plot(coorA[0], coorA[1],'or',ms=20)
    reVect =  coorB - coorA
    kpath_alongAB = []
    normReVect = np.linalg.norm(reVect) #AB
    for index, (k, ucellK) in enumerate(zip(kall, klist)):
      vect = k - coorA # AK
      normVect = np.linalg.norm(vect) 
      normProd = np.linalg.norm(vect)*np.linalg.norm(reVect)
      dotProd = np.dot(reVect, vect)
      #outProd = np.outer(reVect, vect)
      
      angleContained = (np.abs(dotProd - normProd) < toleAngle)
      if angleContained and normVect <= normReVect:
        #print np.linalg.det(outProd), ucellK
        kpath_alongAB.append((index, ucellK, dotProd/np.linalg.norm(reVect) + last))
    last += normReVect
    xticks.append(last)
    kpath.extend(kpath_alongAB)
   
  kpath = pd.DataFrame(kpath, columns=['sc-index','uc-index','distance'])
  kpath = kpath.sort_values(['distance'])
  #kpts = np.array(kpath.values[:,0],dtype=int)

  #kpath.to_csv('selectedKPath.csv')
  
  return xticks, kpath
#  fig, ax = plt.subplots(1,1,figsize=(5,8))
#  ax.plot(kall[kpts,0], kall[kpts,1],'-o',label=str(i))

def readExcitationFile(filename='pwscf.norm.dat'):
  f = open(filename)
  text = f.readlines()
  nbnd, nkstot = [int(i) for i in text[0].split()]
  kweight = [float(i) for i in text[1].split()]
  
  nstep = (len(text) - 2)/(nkstot+1)
  #print nbnd, nkstot, nstep
  del text[1]
  del text[::(nkstot+1)]
  #print text
  #data = np.zeros([nbnd,nkstot,nstep])
  #data = 
  data = np.array([[float(i) for i in line.split()] for line in text])
  data = data[:nstep*nkstot].reshape([nstep, nkstot, nbnd])
  #print data[0,0,:]
  #[ for k in range(nkstot) for step in range(nstep)]
  nocc = int(float(os.popen('grep "number of electrons" result').readline().split()[-1])/2.0)
  
  return data, np.array(kweight), nocc
  
def readTotalEnergy():
  f = os.popen('grep "!    total energy" result')
  energy = np.array([float(line.split()[-2]) for line in f.readlines()])*13.6
  return energy
  
#-------------------------------------------------------------------    
def readEigFile(filename = 'siesta.EIG', sep = False):
  """
  return the Eigenvalues read from systemLabel.EIG
  """
  import math
  eigFile = open(filename)
  line = eigFile.readline()
  EFermi = float(line.split()[0])
  line = eigFile.readline()
  nband= int(line.split()[0])
  nspin= int(line.split()[1])
  nkpt = int(line.split()[2])
  eigen = []
  for kpt in range(nkpt):
    for ispin in range(nspin):
      eigenPerKpt = []
      for iband in range(int(math.ceil(nband/10.0))):
        line = eigFile.readline()
        eigenPerKpt.extend([float(i) for i in line.split()])     
    eigenPerKpt.pop(0)
    eigen.append(eigenPerKpt)
  eigenvalues = np.array(eigen)
  if sep:
    return eigenvalues, EFermi
  else:
    return eigenvalues - EFermi
#-------------------------------------------------------------------
def readEpsilonImaginary(filename = 'siesta.EPSIMG'):
  """
  return the imaginary of epsilon
  """
  epsimgFile = open(filename)
  epsimg = np.array([[float(num) for num in line.split()] 
  for il, line in enumerate(epsimgFile.readlines()) if il > 7])
  return epsimg
#-------------------------------------------------------------------     
def getFermiEnergy():
  """
  return the Fermi Energy read from systemLabel.EIG
  if failed, return 0 rather than raise an exception
  """
  options = tdapOptions()
  systemLabel = options.label
  if os.path.exists(systemLabel+'.EIG'):
    Efermi = float(open(systemLabel+'.EIG').readline().split()[0]) 
  else:
    Efermi = 0.0
  return Efermi
#-------------------------------------------------------------------       
def getCurrent():
#bug
  if os.path.exists('TDEFIELD'):
    Efield = [[float(i) for i in line.split()] for line in open('TDEFIELD')]
    Efield = np.array(Efield)/1E5
    options = tdapOptions()
    timestep = options.tdTimeStep[0]
    time = np.arange(len(Efield))*timestep
  else:
    time = np.zeros(2)
    Efield = np.zeros([2,3])
  return time, Efield 
  
#-------------------------------------------------------------------       
def getEField():
  if os.path.exists('TDEFIELD'):
    Efield = [[float(i) for i in line.split()] for line in open('TDEFIELD')]
    Efield = np.array(Efield)/1E5
    if os.path.exists('input.fdf'):  
        options = tdapOptions()
        timestep = options.tdTimeStep[0]
        time = np.arange(len(Efield))*timestep
    else:
        time, msd = readMSD()
  else:
    time = np.zeros(2)
    Efield = np.zeros([2,3])
  return time, Efield 
#-------------------------------------------------------------------

def getNumOfAtoms():
  import os
  f = os.popen('grep "Number of atoms" -m 1 result')
  numAtom  = int(f.readline().split()[-3])
  f.close()
  return numAtom

def getEnergyTemperaturePressure(ave=False):    
  """
  return the Temperature, KS Energy and Total Energy as the dimension of Nstep
  read from systemLabel.MDE
  returns the Temperature, KS Energy, Total Energy, Volume, Pressure
  """
  options = tdapOptions()
  systemLabel = options.label
  if options.mdTimeStep[0] < 1E-10:
    timestep = options.tdTimeStep[0]
    start = 2
  else:
    start = 0
    timestep = options.mdTimeStep[0]
  if(os.path.exists(systemLabel+'.MDE')):  
      energy_file = open(systemLabel+'.MDE')
      data = []
      for i in energy_file.readlines():
        if i.split()[0]=='#': continue
        data.append([float(j.replace('*','0')) for j in i.split()])
    
      data=np.array(data) 
      if ave:
        numAtom = getNumOfAtoms()
        #print numAtom
        data[start:,2:4] /= numAtom
      #print data
      X = data[:,0]*timestep
      return X[start:], data[start:,1], data[start:,2], data[start:,3], data[start:,4], data[start:,5]
  else:
      time, msd = readMSD()
      f = os.popen('grep "Ekin + Etot (const)" result')
      energy = np.array([float(line.split()[-2]) for line in f.readlines()])*13.6
      #data=np.array([energy,energy,energy,energy,energy]).T
      return time, energy, energy, energy, energy,energy
  
 #-------------------------------------------------------------------
def readMSD(filename='pwscf.msd.dat'):
  f = open(filename)
  text = f.readlines()
  data = np.array([[float(word) for word in line.split()] for line in text])
  return data[:,0]*1E3, data[:,1] 
#-------------------------------------------------------------------  
def getEIGSteps():
  options = tdapOptions()
  steps = []
  for i in os.listdir('.'):
      if i[:6] == 'siesta' and i[-5:] == 'q.EIG':
          steps.append(int(i[6:-5]))

  a = np.array(np.sort(steps),dtype=int)
  #print a  
  return a

#-------------------------------------------------------------------
def getExcitedElectrons(selectK=None, comp = False, ave=False):
  """
  """
  homo = getHomo()
  kpoint,kweight = readKpoints()
  options = tdapOptions()
  selectStep = getEIGSteps()
  #print selectStep
  timestep = options.tdTimeStep[0]
  selectTime = selectStep*timestep
  
  SaveName = 'ExcitedElectrons'
  SaveName1 = 'ExcitedElectrons1'
  exe = loadSaved(SaveName)
  exe1 = loadSaved(SaveName)
  if len(exe) != len(selectStep):
    exe = np.zeros([len(selectStep)])
    exe1 = np.zeros([len(selectStep)])
    for index,step in enumerate(selectStep):
      partition = readEigFile(options.label+str(step)+'q.EIG')
      for i in range(partition.shape[0]):
        partition[i,:] *= kweight[i]
      if selectK is not None: 
        exe[index] = np.sum(partition[selectK,homo:])
      else:
        exe[index] = homo*2 - np.sum(partition[:,:homo])
        exe1[index] = np.sum(partition[:,homo:])
    np.save(SaveName,exe)
    np.save(SaveName1,exe1)
    
  numAtom = getNumOfAtoms()
  if ave:
    exe /= numAtom
    exe1 /= numAtom
  if comp: 
      return selectTime, exe, exe1
  else:
    return selectTime, exe
#-------------------------------------------------------------------
def getAdiabaticEigenvalue(selectK=None):
  """
  """
  options = tdapOptions()
  selectStep = getEIGSteps()
  #print selectStep
  timestep = options.tdTimeStep[0]
  selectTime = selectStep*timestep
  
  SaveName = 'AdiabaticEigenvalue'
  exe = loadSaved(SaveName)
  if len(exe) != len(selectStep):
    exe = []
    for index,step in enumerate(selectStep):
      partition = readEigFile(options.label+str(step)+'.EIG')
      exe.append(partition)
    exe = np.array(exe)
    np.save(SaveName,exe)
  
  return selectTime, exe

#-------------------------------------------------------------------
def getProjectedPartition(selectK=None):
  """
  """
  options = tdapOptions()
  selectStep = getEIGSteps()
  #print selectStep
  timestep = options.tdTimeStep[0]
  selectTime = selectStep*timestep
  
  SaveName = 'ProjectedPartition'
  exe = []
  if len(exe) != len(selectStep):
    exe = []
    for index,step in enumerate(selectStep):
      partition = readEigFile(options.label+str(step)+'q.EIG')
      exe.append(partition)
    exe = np.array(exe)
    np.save(SaveName,exe)
  
  return selectTime, exe
#-------------------------------------------------------------------
def generatePopulationFile(step, ref=True):
  xlabel = 'Energy (eV)'
  ylabel = 'Population'
  
  import pandas as pd
  #dataFilename = xlabel+'vs'+ylabel+'.csv'
  filename = xlabel+'vs'+ylabel+str(step)+'.csv'
  if os.path.exists(filename) and False:
    sortedDF =  pd.read_csv(filename)
  else:
    time, exe = getProjectedPartition()
    time, eigen = getAdiabaticEigenvalue()
    if ref:
      df = pd.DataFrame({xlabel:eigen[step].flatten(),
                         ylabel:(exe[step] - exe[0]).flatten()})
    else:
      df = pd.DataFrame({xlabel:eigen[step].flatten(),
                         ylabel:exe[step].flatten()})
    
    
    sortedDF = df.sort_values(by=xlabel)
    sortedDF.to_csv(filename)
  return sortedDF
  
def calculateDOS(step, xlimits=None, intepNum=1000, bins=200, ref=True, interp= True):
  kcoor, kweight = readKpoints()
  x = np.arange(kcoor.shape[0])
  
  xlabel = 'Energy (eV)'
  ylabel = 'Population'
  
  sortedDF = generatePopulationFile(step,ref)
  
  xt = sortedDF[xlabel]
  yt = sortedDF[ylabel]
  
  #print 'yt is',yt  
  if xlimits != None: 
    x = xt[xt>xlimits[0]][xt<xlimits[1]]
    y = yt[xt>xlimits[0]][xt<xlimits[1]]
  else:
    x = xt
    y = yt
    
  dos, bin_edges = np.histogram(x, bins=bins, range=xlimits)
  par, bin_edges = np.histogram(x, bins=bins, range=xlimits, weights=y/2)
  #parDn, bin_edges = np.histogram(x,bins=bins,range=xlimits,weights=-y/2)
  if not interp:
    return bin_edges[:-1],dos,par
  
  def interp(xin,yin,xout):
    from scipy.interpolate import interp1d
    spline = interp1d(xin, yin, kind='cubic')
    return spline(xout) 
  
  eDosInterp = np.linspace(bin_edges[0], bin_edges[-2], intepNum)
  yDosInterp = interp(bin_edges[:-1], dos, eDosInterp)
  yParInterp = interp(bin_edges[:-1], par, eDosInterp)
  
  return eDosInterp, yDosInterp, yParInterp


def getHomo():
  """
  return the index of the highest occupied molecular orbital (HOMO)
  """
  options = tdapOptions()
  #NumElectron=float(os.popen('grep "Total number of electrons:" result').readline().split()[-1]) 
  NumElectron=float(pythonGrep("Total number of electrons:",'result')[0].split()[-1]) 
  readFile = os.popen('grep -i "SpinPolarized" '+ options.inputFile)
  line = readFile.readline()
  if line == '':
    nspin = 2
  else:
    nspin = 1
  homo = int(NumElectron) // nspin
  return homo
#-------------------------------------------------------------------
def getDipoleFromFile(filename):
  lines = open(filename).readlines()
  dipole = [(float(line.split()[-3]),float(line.split()[-2]),float(line.split()[-1])) for line in lines]
  return np.array(dipole[:-1])
#-------------------------------------------------------------------
def getDipole():
  options = tdapOptions()
  lines = os.popen('grep -n "Electric dipole (a.u.)" result').readlines()    
  dipole = [(float(line.split()[-3]),float(line.split()[-2]),float(line.split()[-1])) for line in lines]
  timestep = options.tdTimeStep[0]
  dipole = np.array(dipole[:-1])
  time = np.arange(len(dipole))*timestep
  return time, dipole
  
#-------------------------------------------------------------------
def getDipolePython():
  options = tdapOptions()
  context = []
  for line in open('result').readlines():
      if len(line) == 1:
          continue
      #print line,
      if 'Electric' in line.split() and 'TDAP' in line.split() :
          context.append(line[:-1])
          
  #for line in context:
  #    print line.split()[-3:]
       
  dipole = [[float(line.split()[-3]),float(line.split()[-2]),float(line.split()[-1])] for line in context]
  #print context
  #dipole = [(float(line.split()[-3]),float(line.split()[-2]),float(line.split()[-1])) for line in lines]
  timestep = options.tdTimeStep[0]
  dipole = np.array(dipole)
  time = np.arange(len(dipole))*timestep
  return np.array(time), np.array(dipole)
#-------------------------------------------------------------------
def getIonicPolarization():
  lines = os.popen('grep -n "The ionic Polarization (a.u.):" result').readlines()    
  dipole = [(float(line.split()[-3]),float(line.split()[-2]),float(line.split()[-1])) for line in lines]
  return np.array(dipole) 
#-------------------------------------------------------------------
def getGaugeFreePolarization():
  lines = os.popen('grep -n "The gauge freedom Polarization" result').readlines()    
  dipole = [(float(line.split()[-3]),float(line.split()[-2]),float(line.split()[-1])) for line in lines]
  return np.array(dipole) 
#-------------------------------------------------------------------
def getElectronPolarization():
  lines = os.popen('grep -n "The electron Polarization (a.u.):" result').readlines()    
  dipole = [(float(line.split()[-3]),float(line.split()[-2]),float(line.split()[-1])) for line in lines]
  return np.array(dipole) 
#-------------------------------------------------------------------
def getEigAndPar(timeSteps=None, forceReread = False):
  """
  return the Times, Eigvalues and Partitions at selected timeSteps
  write two files EIG and PAR
  """
  options = tdapOptions()
  systemLabel = options.label
  timestep = options.tdTimeStep[0]

  if timeSteps == None:
    timeSteps = getEIGSteps()
  time = np.array(timeSteps)*timestep
  
  eig = loadSaved('EIG')
  par = loadSaved('PAR')
  saved = ((len(eig)) != 0 and (len(par)) != 0)
  if (not saved) or forceReread:
    eig = []; par = []
    for i in timeSteps:
      eig.append(readEigFile(systemLabel+str(i)+'.EIG'))
      par.append(readEigFile(systemLabel+str(i)+'q.EIG'))
    eig = np.array(eig)
    par = np.array(par)
    np.save('EIG',eig)
    np.save('PAR',par)
  
  return time, eig, par
#-------------------------------------------------------------------
def getTDEig(timeSteps=None, forceReread = False):
  """
  return the Times, Eigvalues and Partitions at selected timeSteps
  write two files EIG and PAR
  """
  options = tdapOptions()
  systemLabel = options.label
  timestep = options.tdTimeStep[0]
  steps = np.arange(3,options.mdFinalStep)
  
  time = np.array(steps)*timestep
  
  eig = loadSaved('TDEIG')
  saved = ((len(eig)) != 0)
  if (not saved) or forceReread:
    eig=np.array([readEigFile(systemLabel+str(i)+'td.EIG',sep=False) for i in steps])
    np.save('TDEIG',eig)
  
  return time, eig
  
#------------------------------------------------------------------- 
def getVASPBands():  
  f=open('EIGENVAL','r')
  for i in range(5):
  	f.readline()
  
  x,nk,nb=(int(i) for i in f.readline().split())
  #print nk,nb
  bands=np.zeros([nk,nb])
  kpoints=np.zeros([nk,3])
  x=range(nk)
  for i in range(nk):
  	f.readline()
  	coor=f.readline().split()
  	for k in range(3):
  		kpoints[i,k]=float(coor[k])	
  	for j in range(nb):
  		bands[i,j]=float(f.readline().split()[1])
  return x, bands

#------------------------------------------------------------------- 
def getBands(bandType='e'):
  """
  return the bands read from systemLabel.bands as the dimension numKpoint x numBand x numSpin
  returns: X, Ek, xticks, xticklabels
  """  
  import math
  options = tdapOptions()
  systemLabel = options.label
  band_file = open(systemLabel+'.bands')
  if bandType == 'e':
    FermiEnergy = float(band_file.readline().split()[0])
  else:
    band_file.readline()
    FermiEnergy = 0.0
  
  kmin,kmax=(float(i) for i in band_file.readline().split())
  emin,emax=(float(i) for i in band_file.readline().split())
  
  numBand,numSpin,numKpoint=(int(i) for i in band_file.readline().split())
  Ek = np.zeros([numKpoint,numBand,numSpin])
  X = np.zeros(numKpoint)
  
  for kpt in range(numKpoint):
    eigen = []
    for ispin in range(numSpin):
      for iband in range(int(math.ceil(numBand/10.0))):
        line = band_file.readline()
        eigen.extend([float(i) for i in line.split()])  
    X[kpt]=eigen[0]
    eigen.pop()
    Ek[kpt,:,:] = np.array(eigen).reshape(numBand,numSpin) - FermiEnergy #.reshape(1,-1) - EFermi
  
  numSpecK = int(band_file.readline().split()[0])
  xticks = []
  xticklabels =[]
  for i in range(numSpecK):
    line = band_file.readline()
    xticks.append(float(line.split()[0]))
    xticklabels.append(r'$'+line.split()[1][1:-1]+'$')
  
  return X, Ek, xticks, xticklabels
#------------------------------------------------------------------- 
def getDOS(filename = 'siesta.dos'):
  """
  return the dos read from filename as the dimension numEnergyPoint
  returns: energy, up, down, total
  """  
  dosfile = open(filename)
  for i in range(5):
    dosfile.readline()
    
  NumEinter=int(dosfile.readline().split()[2])  
  for i in range(3):
    dosfile.readline()  
  FermiEnergy=float(dosfile.readline().split()[3])
  
  for i in range(3):
    dosfile.readline()
    
  data = []
  for i in range(NumEinter):
    data.append([float(j) for j in dosfile.readline().split()])
   
  data = np.array(data) 
  energy = np.array(data[:,0]) - FermiEnergy
  
  up = np.array(data[:,1])
  down = np.array(data[:,2])
  total = np.array(data[:,3])
  
  return energy, up, down, total

def xv_to_atoms(filename):
    """Create atoms object from xv file.

    Parameters:
        -filename : str. The filename of the '.XV' file.

    return : An Atoms object
    """
    from ase.units import Bohr
    from ase.atoms import Atoms
    if not os.path.exists(filename):
        filename += '.gz'

    with open(filename, 'r') as f:
        # Read cell vectors (lines 1-3)
        vectors = []
        for i in range(3):
            data = f.readline().split()
            vectors.append([float(data[j]) * Bohr for j in range(3)])

        # Read number of atoms (line 4)
        int(f.readline().split()[0])

        # Read remaining lines
        speciesnumber, atomnumbers, xyz, V = [], [], [], []
        for line in f.readlines():
            if len(line) > 5:  # Ignore blank lines
                data = line.split()
                speciesnumber.append(int(data[0]))
                atomnumbers.append(int(data[1]))
                xyz.append([float(data[2 + j]) * Bohr for j in range(3)])
                V.append([float(data[5 + j]) * Bohr for j in range(3)])

    vectors = np.array(vectors)
    atomnumbers = np.array(atomnumbers)
    xyz = np.array(xyz)
    atoms = Atoms(numbers=atomnumbers, positions=xyz, cell=vectors)

    return atoms

  
#-------------------------------------------------------------------
def getTrajactory():
  options = tdapOptions()
  #print(options.laserParam)
  systemLabel = options.label
  NumBlocks=int(os.popen('grep -i %s %s.MD_CAR | wc -l'%(systemLabel, systemLabel)).readline().split()[0])
  position_file = open(systemLabel+'.MD_CAR')
  atomNumList = [int(i) for i in os.popen('head -6 siesta.MD_CAR |tail -1').readline().split()]
  
  numAtomPositionLine = sum(atomNumList)
  totalNumLine = numAtomPositionLine + 7
  
  context = position_file.readlines()
  #import ase.calculators.vasp as vinter
  #from ase.visualize import view
  

  atoms = xv_to_atoms(systemLabel+'.XV')
  atoms.pbc = [True,True,True]
  filename = 'Trajectory'
  from ase.io.trajectory import Trajectory
  if not os.path.exists(filename) or os.path.getmtime(filename) < os.path.getmtime(systemLabel+'.MD_CAR'):
    atomsList = []
    for index in range(NumBlocks):
      output=context[index*totalNumLine:(index+1)*totalNumLine]
      coodinates=np.array([[float(value.replace('\n','')) 
                            for value in line.split()] 
                            for line in output[7:]])
      atomsCurrent = atoms.copy()
      atomsCurrent.set_scaled_positions(coodinates)      
      
      atomsList.append(atomsCurrent)                
      #poscarFileName = "POSCAR"+str(index)
      #poscarFile=open(poscarFileName,'w')
      #poscarFile.writelines(output)
    from ase.io import write  
    write(filename,atomsList,'traj')
  atomsList = Trajectory(filename)
  #print atomsList
  return atomsList
  
def readKpoints():
  options = tdapOptions()
  systemLabel = options.label
  bohr=0.52917721
  filename = systemLabel+'.KP'
  f=open(filename,'r')
  nkpts = int(f.readline().split()[0])
  kcood = [] ; kweight = []
  for i in range(nkpts):
    index, kx, ky, kz, wk = [float(value) for value in f.readline().split()]
    kcood.append((kx,ky,kz))
    kweight.append(wk)
    
  return np.array(kcood)/bohr, np.array(kweight)
#getTrajactory()