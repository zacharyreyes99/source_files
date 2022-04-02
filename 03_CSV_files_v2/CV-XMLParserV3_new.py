import csv
import ssl
import xml.etree.ElementTree as ET
#from xml.dom import minidom

class treeBranch():
    def __init__(self):
        self.ETNode         = []
        self.NodeId         = []
        self.ifcount        = []
        self.loopcount      = []
        self.treeDepth      = []
        self.connCount      = []
        self.dataReadCount  = []
        self.dataWriteCount = []

    def addBlockoEXPR(self, pb):
        self.ETNode.append(pb)
        self.NodeId.append(0)
        self.ifcount.append(0)
        self.loopcount.append(0)
        self.treeDepth.append(0)
        self.connCount.append(0)
        self.dataReadCount.append(0)
        self.dataWriteCount.append(0)

        return len(self.ETNode)-1

    def inc(self,L, i, val): # L = List, from i up to the root, by specific value 
        L=[x+val for x in L[:i]]+ L[i:]

class csvFiles:
    def __init__(self):
        self.t = []   # CSV table i.e., list of dictionary
        self.r = {}   # CSV row i.e., dictionary
        self.h = []   # CSV table headers i.e., list of headers

def uniCode(coID, cicbID, pbID, pID):
    return str(coID) + "-" + str(cicbID) + "-" + str(pbID) + "-" + str(pID)

def csvFileHeaders(f):
    #f.h += []
    f.h = ['uniCode','parent','Tag','Name']
    f.h += ['num_childs','SizeLOC','Num_Code_Blocks']#
    #f.h += ['num-of-local-vars']
    #f.h += ['Num-in-connectors', 'Num-out-connectors']
    #f.h += ['num-of-iterative-loops','num-of-recursive-loops']
    #f.h += ['exec-time', 'call-stack-size']
    #f.h += ['size-of-local-data', 'size-of-global-data']
    #number of incomming connections: external calls to this
    #number of outgoing connections: this calling other functions
    f.h += ['num_variables']
    f.h += ['num_calls']
    f.h += ['num_read_operations']
    f.h += ['num_write_operations']
    f.h += ['num_recursive_calls']
    f.h += ['num_local_calls']
    f.h += ['num_external_calls']
    f.h += ['Nested_Call_Depth']
    f.h += ['List_of_Code_Blocks']#

    f.pf = []
    

def getCndF(s):
    comma  = s.find(',',0) 
    return int(s[1:comma]), int(s[comma+1:-1])

def getcodelines(cLoc):
    comma1  = cLoc.find(',',0) 
    rbrace  = cLoc.find('(',comma1)
    comma2  = cLoc.find(',',rbrace)
    return int(cLoc[1:comma1]), int(cLoc[rbrace+1:comma2])

def getSizeLOC(cLoc1, cLoc2=''):
    L1, L2 = getcodelines(cLoc1)
    
    if cLoc2 !='':
        dummy, l2 = getcodelines(cLoc2)
    return L2 - L1 + 1
    
def savetoCSV(newsitems, filename, fields):

    #print (newsitems, filename, fields)
    with open(filename, 'w', newline='') as csvfile:
        #print ('1 in')
        writer = csv.DictWriter(csvfile, fieldnames = fields)
        #print ('2 in')
        writer.writeheader()
        #print ('3 in')
        writer.writerows(newsitems)

def getCallType(A, H):
    cA, fA = getCndF(A)
    cH, fH = getCndF(H)
    if cA == cH:
        if fA == fH:
            return 'Recursive'
        else:
            return 'Local'
    else:
        return 'External'

def parseData(Dp): # Dp = data point, returns nVr, nVw, nCr, nCl, nCe, CnD
    '''
      Dp = data point, 
      returns [
        nV  ->> number of  variables
        nC  ->> number of calls
        nVr ->> number of read operations
        nVw ->> number of write operations
        nCr ->> number of recursive calls
        nCl ->> number of local calls
        nCe ->> number of external calls
        CnD ->> Nested Call Depth
        ]
    '''
    dataL = [0 for x in range (8)] # for nV, nC, nVr, nVw, nCr, nCl, nCe, CnD.
    xnV, xnC, xnVr, xnVw, xnCr, xnCl, xnCe, xCnD = range(8)

    for p in Dp:
        if p.tag == 'Variable':
            dataL[xnV]+=1
            if p.attrib['Access']=="Read":
                dataL[xnVr]+=1
            else:
                dataL[xnVw]+=1
        elif p.tag == 'Call':
            dataL[xnC]+=1
            dataL[xCnD] += 1
            CallType = getCallType(p.attrib['Access_block'], p.attrib['Home_block'])
            if CallType=='Recursive':
                dataL[xnCr]+= 1
            elif CallType=='Local':
                dataL[xnCl]+= 1
            else:
                dataL[xnCe]+= 1
            if len(p)>0:
                _dataL = parseData(p)
                dataL = [dataL[x] + _dataL[x] for x in range (len(dataL))]

        elif p.tag == 'Data':
            if len(p)>0:
                _dataL = parseData(p)
                dataL = [dataL[x] + _dataL[x] for x in range (len(dataL))]
        else:
            print ("Impossible 3dffe")

    return dataL

def parsePB(coID, cicbID, parent, pb, b): # pB= point Block, p = (for recursion) sublist of CSVdataofPB, f = CSVfiles, b = treebranch [root->current node]
    BlockIndex = b.addBlockoEXPR(pb)    
    r = {}
    pL =[]
    r['parent']= parent    
    b.inc(b.treeDepth, BlockIndex, 1)

    i = 1  # Local counter 
 
    ACCUdataL = [0 for x in range (8)] # for nV, nC, nVr, nVw, nCr, nCl, nCe, CnD

    for p in pb:
        nestedL = []
        pCBlist = []
        dataL = [0 for x in range (8)] # for nV, nC, nVr, nVw, nCr, nCl, nCe, CnD 

        #if len(p)>0: r['Id'] = i        
        
        #r['Id'] = i #nextpB
        r['uniCode']= uniCode(coID, cicbID, BlockIndex, i)
        numChilds = 0

        if p.tag=='Conditional':
            r['Tag']= 'B'
            r['Name']= 'if'
            r['SizeLOC']= getSizeLOC(p.attrib['Code_Loc'])            
            b.inc(b.ifcount, BlockIndex, 1)
            if len(p)>0:
                if p[0].tag == 'Point_Block':
                    #--------------
                    for y in p:  # No Need for loop here
                        l,k,dataL = parsePB(coID, cicbID, r['uniCode'], y, b)
                        nestedL += l
                        pCBlist += k
                        numChilds += len(y)
                else:
                    print ("Impossible 35f")
        elif p.tag=='Selective':
            r['Tag']= 'B'
            r['Name']= 'if-else/switch'
            r['SizeLOC']= getSizeLOC(p.attrib['Code_Loc'])

            b.inc(b.ifcount, BlockIndex, 1)
            if len(p)>0:
                if p[0].tag == 'Point_Block':
                    for y in p:  # No Need for loop here
                        l,k,dataL = parsePB(coID, cicbID, r['uniCode'], y, b)
                        nestedL += l
                        pCBlist += k
                        numChilds += len(y)
                else:
                    print ("Impossible 4443")
        elif p.tag=='Cyclic':
            r['Tag']= 'L'
            r['Name']= 'for/while'
            r['SizeLOC']= getSizeLOC(p.attrib['Code_Loc'])

            b.inc(b.loopcount, BlockIndex, 1)
            if len(p)>0:
                if p[0].tag == 'Point_Block':
                    for y in p:  # No Need for loop here
                        l,k,dataL = parsePB(coID, cicbID, r['uniCode'], y, b)
                        nestedL += l
                        pCBlist += k
                        numChilds += len(y)
                else:
                    print ("Impossible fr4")
        elif p.tag=='Data': 
            r['Tag']= 'D'
            r['Name']= 'Assignment'
            r['SizeLOC'] = getSizeLOC(p.attrib['Code_Loc'])
            dataL = parseData(p)
            numChilds = len(p)
            #print ('---------->>', nV, nC, nVr, nVw, nCr, nCl, nCe, CnD)
        #elif p.tag=='Call':
            #b.inc(b.connCount, BlockIndex, 1)
        else: 
            print ("Impossible 667")

        r['num_childs']= numChilds
        r['num_variables']=dataL[0]
        r['num_calls']= dataL[1]
        r['num_read_operations']= dataL[2]
        r['num_write_operations']= dataL[3]
        r['num_recursive_calls']= dataL[4]
        r['num_local_calls']=dataL[5]
        r['num_external_calls']= dataL[6]
        r['Nested_Call_Depth']= dataL[7]

        ACCUdataL =[ACCUdataL[x] + dataL[x] for x in range (len(ACCUdataL))]
        #print('))------------------>r=' , r.values())
        #---------------------------------------------------------------
        r['Num_Code_Blocks']= len(pCBlist)
        r['List_of_Code_Blocks']= pCBlist
        #---------------------------------------------------------------

        pL.append(r.copy())
        pL= pL + nestedL
  
        i += 1    
    return pL, [BlockIndex], ACCUdataL
     

def parseXML(xmlfile, f, b):

    csvFileHeaders(f)
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    CompRow ={}
    CompIndex = b.addBlockoEXPR(root)
    CompRow['parent']= ''
    #CompRow['Id']= root.attrib['Id']
    CompID= root.attrib['Id']
    CompRow['uniCode']= uniCode(CompID, 0, 0, 0)
    CompRow['Tag']= 'C'
    CompRow['Name']= root.attrib['Name']

    b.inc(b.treeDepth, CompIndex, 1)

    CompRow['num_childs']= root.attrib['Num_CICBs']
    #print('))------------------>CompRow=' , CompRow.values())

    #-------------------------------------------------------        
    if int(root.attrib['Num_CICBs']) <= 0: exit() 
    
    MasterRows, MasterCBlist, MasterdataL = parsePB(CompID, 0, CompRow['uniCode'], root[0][2], b) #Parent Id, PBId, ETRef, CSVLst, branch(node->root)
    xMasterCBlist = []
 
    ACCUdataL = [0 for x in range (8)] # for nV, nC, nVr, nVw, nCr, nCl, nCe, CnD

    if len(root)>1:
        for CICB in root[1:]:
            CICBRow = {}
            
            CICBIndex = b.addBlockoEXPR(CICB)
            CICBRow['parent']= CompRow['uniCode']
            #CICBRow['Id']= CICB.attrib['Id']
            CICBID =CICB.attrib['Id']
            CICBRow['uniCode']= uniCode(CompID, CICBID, 0, 0)
            CICBRow['Tag']= 'F'
            CICBRow['Name']= CICB.attrib['Name']
            b.inc(b.treeDepth, CICBIndex, 1)

            CICBRow['num_childs']= len(CICB[2])        
            CICBRow['SizeLOC']= getSizeLOC(CICB[2].attrib['Code_Loc'])

            #print('))------------------>CICBRow=' , CICBRow.values())
            
            #count=0
            #for x in CICB[2].findall('Cyclic'): count +=1
            #brow['num-of-iterative-loops']= count            

            #-------------------------------------------------------
            pbRowssss, CBlist, pbdataL = parsePB(CompID, CICBID, CICBRow['uniCode'], CICB[2], b) #Parent Id, PBId, ETRef, CSVLst, branch(node->root)      
            xMasterCBlist  += CBlist
            #-------------------------------------------------------
            
            CICBRow['num_variables']=pbdataL[0]
            CICBRow['num_calls']= pbdataL[1]
            CICBRow['num_read_operations']= pbdataL[2]
            CICBRow['num_write_operations']= pbdataL[3]
            CICBRow['num_recursive_calls']= pbdataL[4]
            CICBRow['num_local_calls']=pbdataL[5]
            CICBRow['num_external_calls']= pbdataL[6]
            CICBRow['Nested_Call_Depth']= pbdataL[7]

            CICBRow['Num_Code_Blocks']= len(CBlist)
            CICBRow['List_of_Code_Blocks']= CBlist

            ACCUdataL =[ACCUdataL[x] + pbdataL[x] for x in range (len(ACCUdataL))]
            f.t = f.t + [CICBRow] 
            f.t = f.t + pbRowssss

    #print (f.t) 
    
    f.t = MasterRows + f.t

    CompRow['SizeLOC']= getSizeLOC(root[0][2].attrib['Code_Loc'], root[len(root)-1][2].attrib['Code_Loc'])

    CompRow['num_variables']=ACCUdataL[0]
    CompRow['num_calls']= ACCUdataL[1]
    CompRow['num_read_operations']= ACCUdataL[2]
    CompRow['num_write_operations']= ACCUdataL[3]
    CompRow['num_recursive_calls']= ACCUdataL[4]
    CompRow['num_local_calls']=ACCUdataL[5]
    CompRow['num_external_calls']= ACCUdataL[6]
    CompRow['Nested_Call_Depth']= ACCUdataL[7]

    CompRow['Num_Code_Blocks']= len(xMasterCBlist)  
    CompRow['List_of_Code_Blocks']= xMasterCBlist
    f.t = [CompRow] + f.t
    
    savetoCSV(f.t, 'comp' + CompID + '-Nodes.csv', f.h)
    #-------------------------------------------------------
      
def main():   
    import os

    cvfs = csvFiles()
    b = treeBranch()


    XMLs = []
    for root, dir, files in os.walk('.'):
        for f in files:
            if f.endswith('.xml'):
                # parse xml file                
                if f !='0-sys-components.xml':
                    parseXML(f, cvfs, b)
                    cvfs = csvFiles()
    
    print ('Done ..........................................')
      
if __name__ == "__main__":
  
    # calling main function
    main()



##Parent            : Parent ID
##Id	              : Auto--INJection style - Unique
##Tag                 : Comp/CICB/CodeBlock/Selective/...  
##Name	              : Name 
##num-of-childs       : Num_CICBs |nested statement
##SizeLOC             : Size 
##exec-time	
##call-stack-size	
##num-of-local-vars	
##size-of-local-data	
##size-of-global-data	
##Num-in-connectors	
##Num-out-connectors	
##num-of-iterative-loops	
##num-of-recursive-loops
