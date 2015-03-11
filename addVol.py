#!/usr/bin/python
import os,sys
import datetime

stdFreeSize=19
#volSize='1M'
volSize='600G'


def getDBName():
#	database_file=open('/home1/cubrid2/CUBRID/databases/databases.txt')
	database_file=open('/home1/cubrid2/CUBRID/databases/databases2.txt')
	i=0
	dbName_temp=[]

	for db in database_file.read().splitlines():
		temp=db.split()
		dbName_temp.append(temp[0])

	dbName=dbName_temp[1:]
	database_file.close()
	return dbName


def checkCubVer():
	spCmd='cubrid_rel > cubVer.txt'
	os.system(spCmd)

	ver_file=open('cubVer.txt')
	cub_ver_temp=ver_file.read().splitlines()
	cub_ver_temp2=cub_ver_temp[1].split()
	cub_ver=cub_ver_temp2[3].strip('(').strip(')')[0:3]

	ver_file.close()

	return cub_ver


def checkFreeSpace(dbName):
	spCmd='cubrid spacedb '+ dbName + '@localhost -s > sp.txt'
	os.system(spCmd)

	spFile=file('sp.txt')
	volDict={}
	for volInfo in spFile.read().splitlines():
		temp=volInfo.split()

		if len(temp)>0 and temp[0]=='DATA':
			volDict['DATA']=temp[5]+temp[6]
		elif len(temp)>0 and temp[0]=='INDEX':
			volDict['INDEX']=temp[5]+temp[6]

	spFile.close()
	return volDict


def getVolName(dbName, volType):
	spCmd='cubrid spacedb '+ dbName +'@localhost |grep ' + volType + ' > spd_' + volType +'.txt'
	os.system(spCmd)

	spdFile=file('spd_'+volType+'.txt')
	cont_list=[]
	rowCnt=spdFile.read().count('\n')
	spdFile.seek(0)

	for line in spdFile.read().splitlines():
		cont_list.append(line)

	alist=range(0,rowCnt)
	alist.reverse()

	for idx in alist:
		idx_list=cont_list[idx].split()

		if idx_list[1]==volType:
			total_name=idx_list[6]
			div_idx=total_name.rfind('/')+1
			file_name_temp=total_name[div_idx:]
			file_name=file_name_temp[0:-3]+str(int(file_name_temp[-3:])+1).zfill(3)
			file_path=total_name[0:div_idx]

			return file_path, file_name
			break
	spdFile.close()


def addVol(dbName, volType, filePath, fileName,cubVersion):
	log=open('addVol.log','a')

	if cubVersion =='9.2':
		spCmd='cubrid addvoldb -p ' + volType + ' -F ' + filePath + ' -n ' + fileName + ' ' + dbName + '@localhost --max-writesize-in-sec=50M' + ' --db-volume-size=' + volSize

	else:
		spCmd='cubrid addvoldb -p ' + volType + ' -F ' + filePath + ' -n ' + fileName + ' ' + dbName + '@localhost' + ' --db-volume-size=' + volSize

	result=os.system(spCmd)

	logWrite(spCmd + '\n' + str(result))
	
	log.close()
#	print spCmd
	return result

def logWrite(msg):
	log=open('addVol.log','a')

	now=datetime.datetime.now()
	log.writelines('='*60)
	log.writelines('\n')
	log.writelines(str(now))
	log.writelines('\n')
	log.writelines(msg)
	log.writelines('\n')


def checkIOwait():
	pass
		

def checkDiskFree(mountPoint):
	os.system('df -h > df.out')
	df_file=open('df.out')
	dfDict={}

	for f in df_file.read().splitlines():
		if f.split()[5] == mountPoint:
			tList=f.split()
			break

#	if tList[3][-1:]==volSize[-1:] and tList[3][0:-1] > volSize[0:-1]:
	if tList[3][0:-1] > volSize[0:-1]:
		return 0
	else:
		logWrite('Insufficient free space !!!' + '\n' + mountPoint + ' : ' + tList[3][0:-1] + tList[3][-1:])
		return 1
	

if __name__=="__main__":
	dbList=getDBName()
	cubVer=checkCubVer()

	for dbName in dbList:
		vol_dict=checkFreeSpace(dbName)
#		print vol_dict
		dataFreeSize=vol_dict['DATA']
		indexFreeSize=vol_dict['INDEX']


		if float(vol_dict['DATA'][0:-1]) < stdFreeSize:
			dataVol=getVolName(dbName, 'DATA')
			mountPoint=dataVol[0][0:dataVol[0].find('/',1)]
			print mountPoint
			result=checkDiskFree(mountPoint)
			print result
#			print dataVol
			addVol(dbName, 'DATA', dataVol[0], dataVol[1], cubVer)

		
		if float(vol_dict['INDEX'][0:-1]) < stdFreeSize:
			indexVol=getVolName(dbName, 'INDEX')
			mountPoint=indexVol[0][0:indexVol[0].find('/',1)]
			print mountPoint
			result=checkDiskFree(mountPoint)
			print result
#			print indexVol
			if result==0:
				addVol(dbName, 'INDEX', indexVol[0], indexVol[1], cubVer)
	
#	c=checkDiskFree('/home1')
#	print c

