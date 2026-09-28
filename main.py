from map import Zone ,StaticMap
from parsed import Parse
import sys
def main()->None:
    arguments=sys.argv[1:]
    par=Parse()
    if len(arguments) != 1:
        print("not one argument")
        return
    elif len(arguments[0])==0:
        print("name of file empty")
        return
    else:
        lines,error=par.read_file(arguments[0])
        if error :
            print(error)
        mapdri,erros=par.verfier_values(lines)
        if error:
            for er in erros:
                print(er)
        else:
            print(mapdri.print_hubs())
if __name__ =="__main__":
    main()