# Vitosoft Software

[Vitosoft 300 Typ SID1](https://connectivity.viessmann.com/de/mp-fp/vitosoft.html) is available from Viessmann. It is only available for Windows.

It requires an OptoLink/USB adapter or a system with an integrated WLAN interface.

There is a 90 day [demo version](https://connectivity.viessmann.com/content/dam/public-micro/connectivity/vitosoft/de/Vitosoft-300-SID1-Setup.zip/_jcr_content/renditions/original.media_file.download_attachment.file/Vitosoft-300-SID1-Setup.zip) available.

The version is outdated and requires updating directly after installation.

These are the known versions:
- Release 6.1.0.2 (15.12.2015) - available at [http://update.vitosoft.de/CurrentVersion/Vitosoft300SID1_Setup.exe](http://update.vitosoft.de/CurrentVersion/Vitosoft300SID1_Setup.exe) or inside [https://update-vitosoft.viessmann.com/CurrentVersion/Vitosoft300WithoutDocs.iso](https://update-vitosoft.viessmann.com/CurrentVersion/Vitosoft300WithoutDocs.iso) as the file `Vitosoft300SID1_Fallback_Setup.exe`
- Release 7.1.4.8 (21.10.2016)
- Release 8.0.5.0 (12.07.2017) - available at [https://connectivity.viessmann.com/](https://connectivity.viessmann.com/content/dam/vi-micro/CONNECTIVITY/Vitosoft/Vitosoft300SID1_Setup.exe/_jcr_content/renditions/original.media_file.download_attachment.file/Vitosoft300SID1_Setup.exe)
- Release 8.0.6.2 (14.12.2017)- The demo link gets you this version.

As you can see, there seem to be no new updates for 3.5 years.

Even if you have no intention in running the software, you need to download it and extract several XML files from it, which contain all information about what data points are available for which system. To extract the `EXE` file, you need to use 7-Zip (7z on UNIX). On a Macintosh, it can be installed via `brew install p7zip`. The easiest is to copy the `EXE` file into a new directory, and then run the following terminal command inside the directory:

	7z e Vitosoft300SID1_Setup.exe -r "*.xml" -y

*WARNING*: This is only for testing! For get the real production XML files from Vitosoft, it is essential to run Vitosoft _once_ for this file to be generated correctly – otherwise you have a very outdated versions of the following files. All the other XML files are identical.

- `C:\Program Files\Viessmann Vitosoft 300 SID1\ServiceTool\MobileClient\Config\ecnDataPointType.xml`
- `C:\Program Files\Viessmann Vitosoft 300 SID1\ServiceTool\MobileClient\Config\ecnEventType.xml`
- `C:\Program Files\Viessmann Vitosoft 300 SID1\ServiceTool\MobileClient\Config\ecnVersion.xml`


## Software update mechanism

The software checks and downloads new versions at launch via 3 Soap requests.

### CheckSoftwareVersion

**Endpoint**: POST - https://update-vitosoft.viessmann.com/vrimaster/VRIMasterWebService.asmx

**Description**: Send the current version and check if a newer version is available. In this example the License info is from the trial version.

#### Header
```
{
	User-Agent: Mozilla/4.0 (compatible; MSIE 6.0; MS Web Services Client Protocol 4.0.30319.42000)
	Content-Type: text/xml; charset=utf-8
	SOAPAction: "http://www.e-controlnet.de/services/VRIMasterWebService/CheckSoftwareVersion"
	Host: update-vitosoft.viessmann.com
	Accept-Encoding: gzip, zlib, deflate, zstd, br
}
```


#### Body
```
<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><CheckSoftwareVersion xmlns="http://www.e-controlnet.de/services/VRIMasterWebService"><client><CustomerId>90 Tage Testlizenz</CustomerId><MaintenanceContractEndTime>0001-01-01T00:00:00</MaintenanceContractEndTime></client><licenceInfo><LicenceId>1063</LicenceId><LicenceHash>B25913BD9D042609498C93AC6DA797D8</LicenceHash><CustMajorVersion /><CID>008785F19C4F1A485EAFF715026860E2</CID></licenceInfo><softwareVersion><ClientSoftwareVersion>6.1.0.2</ClientSoftwareVersion></softwareVersion></CheckSoftwareVersion></soap:Body></soap:Envelope>
```

### RequestDownload

**Endpoint**: POST - https://update-vitosoft.viessmann.com/vrimaster/VRIMasterWebService.asmx

**Description**: Request the download of a new version. This response with a token UUID, which is valid for 24 hours to download the new version.

#### Header
```
{
	content-type: text/xml; charset=utf-8
	Accept-Encoding: gzip, zlib, deflate, zstd, br
}
```

#### Body
```
<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><RequestDownload xmlns="http://www.e-controlnet.de/services/VRIMasterWebService"><client><CustomerId>90 Tage Testlizenz</CustomerId><MaintenanceContractEndTime>0001-01-01T00:00:00</MaintenanceContractEndTime></client><licenceInfo><LicenceId>1063</LicenceId><LicenceHash>B25913BD9D042609498C93AC6DA797D8</LicenceHash><CustMajorVersion /><CID>008785F19C4F1A485EAFF715026860E2</CID></licenceInfo><downloadType>Software</downloadType></RequestDownload></soap:Body></soap:Envelope>
```

#### Response
```
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <RequestDownloadResponse xmlns="http://www.e-controlnet.de/services/VRIMasterWebService">
      <RequestDownloadResult>
        <OperationSuccess>true</OperationSuccess>
        <OperationMessage>token created</OperationMessage>
        <OperationCode>0</OperationCode>
        <Token>
          <Value>d7d60ea5-47c2-4a9f-8358-ae06e7a50bca</Value>
          <CreationTime>2021-01-01T12:00:00.0000000+02:00</CreationTime>
          <ValidTime>2021-01-02T12:00:00.0000000+02:00</ValidTime>
        </Token>
      </RequestDownloadResult>
    </RequestDownloadResponse>
  </soap:Body>
</soap:Envelope>
```

### DownloadSoftware

**Endpoint**: POST - https://update-vitosoft.viessmann.com/vrimaster/VRIMasterWebService.asmx

**Description**: With the token from the `RequestDownload` call, generate a URL to download the update. Strangely neither the UUID now the expiry is important. It seems the server completely ignore them. The UUID can be found again inside the generated URL, which points to an `EXE` file for a full installer of the software.

#### Header
```
{
	x-aspnet-version: 2.0.50727
	content-type: text/xml; charset=utf-8
	date: Tue, 20 Jul 2021 13:43:35 GMT
	p3p: CP="NON CUR OTPi OUR NOR UNI"
	server: Microsoft-IIS/10.0
	cache-control: private, max-age=0
	x-powered-by: ASP.NET
	Accept-Encoding: gzip, zlib, deflate, zstd, br
}
```

#### Body
```
<?xml version="1.0" encoding="utf-8"?><soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"><soap:Body><DownloadSoftware xmlns="http://www.e-controlnet.de/services/VRIMasterWebService"><token><Value>d7d60ea5-47c2-4a9f-8358-ae06e7a50bca</Value><CreationTime>2021-01-01T12:00:00.0000000+02:00</CreationTime><ValidTime>2021-01-02T12:00:00.0000000+02:00</ValidTime></token><softwareVersion><ClientRequestSoftwareVersion>8.0.6.2</ClientRequestSoftwareVersion></softwareVersion></DownloadSoftware></soap:Body></soap:Envelope>
```

#### Response
```
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <DownloadSoftwareResponse xmlns="http://www.e-controlnet.de/services/VRIMasterWebService">
      <DownloadSoftwareResult>
        <OperationSuccess>true</OperationSuccess>
        <OperationMessage>installer generated</OperationMessage>
        <OperationCode>0</OperationCode>
        <URL>http://update.vitosoft.de/VRIMasterWebService/Software/CustomerSoftware/d7d60ea5-47c2-4a9f-8358-ae06e7a50bca/8.0.6.2%20637625575615728917.exe</URL>
      </DownloadSoftwareResult>
    </DownloadSoftwareResponse>
  </soap:Body>
</soap:Envelope>
```
