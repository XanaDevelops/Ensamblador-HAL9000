import sys

class InvalidSyntax(Exception):
    pass
class InvalidOPCode(Exception):
    pass

class HALAS():
    version:str = "1.0.1"

    rutaArchivo :str =""
    ops:list = "LOA STO LOIP STIP GOI GOZ GON EXIT COPY ADD SUB AND SET ADQ LSH".split(" ")
    opsCode:list = "0000 0001 0010 0011 0100 0101 0110 10 11000 11001 11010 11011 11100 11101 11110".split(" ")
    etiquetas:dict
    registros = {"T0":0, "T1":1, "X2":2, "X3":3, "X4":4, "X5":5, "X6":6, "X7":7}
    

    def __init__(self) -> None:
        print("******  ENSAMBLADOR PARA HAL9000 por Daniel G *******\n")
        if(len(sys.argv)>1): #se ha pasado archivo
            self.rutaArchivo = sys.argv[1]
        else:
            self.rutaArchivo = input("Introduce nombre del archivo fuente: ")
            #self.rutaArchivo = "./caso0.txt"
        try:
            self.asemblar()
        except OSError:
            print("Ese archivo no existe", sys.stderr)
            exit(1)
        except (InvalidSyntax, InvalidOPCode, ValueError) as ex:
            print(type(ex), ex)



    def asemblar(self):
        hexs:list =[]
        self.etiquetas = dict()
        lineas:list
        with open(self.rutaArchivo, "r") as f:
            lineas = f.readlines()

        for i in range(len(lineas)):
            lineas[i] = lineas[i].replace("\n","")

        self.setEtiquetas(lineas)
        print("Etiquetas", self.etiquetas)

        for linea in lineas:
            op:int  = self.getOpId(linea)
            #print(op)
            match op:
                case 0 | 1:
                    hexs.append(self.LOASTO(linea, op))
                case 2 | 3:
                    hexs.append(self.LOIPSTIP(linea, op))
                case 4 | 5 | 6:
                    hexs.append(self.GO(linea, op))
                case 7:
                    hexs.append(self.EXIT(linea))
                case 8:
                    hexs.append(self.COPY(linea))
                case 9 | 10 | 11:
                    hexs.append(self.ADDSUBAND(linea, op))
                case 12 | 13:
                    hexs.append(self.SETADQ(linea, op))
                case 14:
                    hexs.append(self.LSH(linea))
                case -1:
                    hexs.append(self.MemValue(linea))
                case None:
                    continue
            
        res:str = "EMEM:\tDC.W "
        lcount:int = 0
        for x in hexs:
            res+= f"${x},"
            if(lcount>9):
                lcount=0
                res+="\n\tDC.W "
            else:
                lcount+=1
        res+="\n"
        res = res.replace(",\n","\n")
        print(res)

    def LOASTO(self, linea:str, op:int) -> str:
        res:str = self.opsCode[op]
        res+="000"

        factores:list = linea.split(" ")

        factores = self.cleanFactores(factores)

        memvalue = factores[op]
        if(memvalue.isnumeric()): #valor absoluto
            memvalue = int(memvalue)
            if memvalue>=2**8:
                raise ValueError("Valor absoluto excede 2^8 bits")
            res+=bin(memvalue)[2:].zfill(8)
        else:
            if(memvalue not in self.etiquetas.keys()):
                raise InvalidSyntax("Etiqueta no definida", memvalue)
            res += bin(self.etiquetas[memvalue])[2:].zfill(8)

        ti = factores[1-op]
        if(ti not in ["T0", "T1"]):
            raise InvalidSyntax("Registro no valido", ti)
        
        res +=bin(int(ti[1]))[2:]
        #print(res)
        return hex(int(res, 2))[2:].upper().zfill(4)


    def LOIPSTIP(self, linea:str, op:int) -> str:
        res:str = self.opsCode[op]
        res+="00000"

        factores:list = linea.split(" ")

        factores = self.cleanFactores(factores)

        reg = factores[op-2]
        if(reg[0]!="(" and reg[-1] != ")" and reg[1:3] not in self.registros.keys()):
            raise InvalidSyntax("Direccionamiento invalido", reg)
        res+=bin(self.registros[reg[1:3]])[2:].zfill(3)
        res+="000"

        ti = factores[1-(op-2)]
        if(ti not in ["T0", "T1"]):
            raise InvalidSyntax("Registro no valido", ti)
        
        res +=bin(int(ti[1]))[2:]

        #print(op, res.zfill(16))
        return hex(int(res, 2))[2:].upper().zfill(4)


    def GO(self, linea:str, op:int) -> str:
        res:str = self.opsCode[op]
        res+="000"

        factores:list = linea.split(" ")

        factores = self.cleanFactores(factores)

        memvalue = factores[0]
       
        if(memvalue.isnumeric()): #valor absoluto
            memvalue = int(memvalue)
            if memvalue>=2**8 or memvalue<0:
                raise ValueError("Rango memoria invalido: ",memvalue)
            res+=bin(memvalue)[2:].zfill(8)
        else:
            if(memvalue not in self.etiquetas.keys()):
                raise InvalidSyntax("Etiqueta no definida", memvalue)
            
            res += bin(self.etiquetas[memvalue])[2:].zfill(8)

        res+="0"

        return hex(int(res, 2))[2:].upper().zfill(4)

    

    def EXIT(self, linea:str) -> str:
        return hex(int("1"+"0"*15,2))[2:].zfill(4)

    def COPY(self, linea:str) -> str:
        res:str = self.opsCode[8]
        res+= "0000"
        factores:list = linea.split(" ")

        factores = self.cleanFactores(factores)
        for i in range(2):
            reg = factores[i]
            if(reg not in self.registros.keys()):
                raise InvalidSyntax("registro no valido", reg)
            res+=bin(self.registros[reg])[2:].zfill(3)
            res+="0"

        res = res[:-1]
        #print(res)
        return hex(int(res, 2))[2:].upper().zfill(4)

    def ADDSUBAND(self, linea:str, op:int) -> str:
        res:str = self.opsCode[op]

        factores:list = linea.split(" ")

        factores = self.cleanFactores(factores)

        for i in range(3):
            reg = factores[i]
            if(reg not in self.registros.keys()):
                raise InvalidSyntax("registro no valido", reg)
            res+=bin(self.registros[reg])[2:].zfill(3)
            res+="0"
        res = res[:-1]
        #print(res)
        return hex(int(res, 2))[2:].upper().zfill(4)


    def SETADQ(self, linea:str, op:int) -> str:
        res:str = self.opsCode[op]

        factores:list = linea.split(" ")

        factores = self.cleanFactores(factores)

        k:str = factores[0]
        if(k[0]!="#" and not self.isNum(k[1:])):
            raise ValueError("Absoluto no valido", k)
        k:int = int(k[1:])
        if( -2**7>k or k>=2**7):
            raise ValueError("Absoluto fuera de rango",k)
        res+=self.getAbsC2(k, 8) 

        reg = factores[1]
        if(reg not in self.registros.keys()):
            raise InvalidSyntax("registro no valido", reg)
        res+=bin(self.registros[reg])[2:].zfill(3)
        #print(res)
        return hex(int(res, 2))[2:].upper().zfill(4)

        
    def LSH(self, linea:str) -> str:
        res:str = self.opsCode[14]

        factores:list = linea.split(" ")

        factores = self.cleanFactores(factores)

        p:str = factores[0]
        if(p[0]!="#" and not p[1:].isnumeric()):
            raise InvalidSyntax("Absoluto no valido", p)
        p:int = int(p[1:])
        if(p>=2**3 or p<0):
            raise InvalidSyntax("Absoluto fuera de rango: ",p)
        res+=self.getAbsC2(p, 3)
        res+="0"

        reg = factores[1]
        if(reg not in self.registros.keys()):
            raise InvalidSyntax("registro no valido", reg)
        res+=bin(self.registros[reg])[2:].zfill(3)
        res+="000"

        n:str = factores[2]
        if(n[0]!="#" and not n[1:].isnumeric()):
            raise ValueError("n debe ser #0 o #1, no", n)
        n:int =int(n[1:])
        if(n<0 or n>2):
            raise ValueError("n debe ser #0 o #1, no", n)
        res+=bin(n)[2:]

        #print(res)
        return hex(int(res, 2))[2:].upper().zfill(4)

    def MemValue(self, linea:str):
        factores:list = linea.split(" ")
        if(":" in factores[0]): #tiene etiqueta
            factores.pop(0)
        while(factores[0]==""): #tiene basura en medio
            factores.pop(0)

        v = factores[0]
        if(not self.isNum(v)):
            raise ValueError("eso no es un numero decimal", v)
        v:int = int(v)

        if(abs(v) >=2**16):
            raise ValueError("rango invalido", v)
        
        if(v<0):
            v=2**16+v
        return hex(v)[2:].zfill(4).upper()

    def setEtiquetas(self, lineas:list) -> None:
        memdir:int = 0
        for linea in lineas:
            factores:list = linea.split(" ")
            if(":" in factores[0]): #tiene etiqueta
                self.etiquetas.update({factores[0].replace(":", ""):memdir})
            memdir+=1

    def getOpId(self, linea:str) -> int:
        i:int = 0
        factores:list = linea.split(" ")
        if(factores[0]=='' and len(factores)==1):
            print("Linea vacia")
            return None
        if(":" in factores[0]): #tiene etiqueta
            i+=1
        while(factores[i]==""):
            factores.pop(i)

        if(self.isNum(factores[i])): #se trata de un valor de memoria
            return -1
        if factores[i] not in self.ops:
            raise InvalidOPCode("OP desconocido:", factores[i])
        return self.ops.index(factores[i])

    def getAbsC2(self, v:int, l:int) -> str:
        if (v>=0):
            return ("0"+bin(v)[2:]).zfill(l)
        else:
            r=bin((v*-1-1))[2:]
            r=r.replace("0","2")
            r=r.replace("1","0")
            r=r.replace("2", "1")
            r="1"*(l-len(r))+r
            return r
        
    def isNum(self, valor:str) -> bool:
        if valor.isnumeric():
            return True
        if valor[0] == "-" and valor[1:].isnumeric():
            return True
        return False

    def cleanFactores(self, factores) -> list:
        if(":" in factores[0]): #tiene etiqueta
            factores.pop(0)
        while(factores[0]==""): #tiene basura en medio
            factores.pop(0)
        factores.pop(0) #eliminar mnenomico

        for i in range(len(factores)):
            factores[i] = factores[i].replace(",","")
        
        return factores


if __name__ == "__main__":
    HALAS()