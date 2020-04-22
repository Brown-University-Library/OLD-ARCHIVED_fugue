<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xs="http://www.w3.org/2001/XMLSchema"
	xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
	xmlns:xlink="http://www.w3.org/1999/xlink"
    
    exclude-result-prefixes="xs xd"
    version="1.1">
  
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  
  <xsl:param name="output_dir"/>
  <xsl:param name="output_uri_root"/>
  
  <xsl:template match='/'>
    <xsl:apply-templates select="//data-sources/docpages/file"/>
  </xsl:template>

  <xsl:template match='data-sources/docpages/file'>
    <xsl:variable name="outfile" select="concat($output_dir, '/', ./@filestem, '.html')"/>
    <xsl:value-of select="."/>
    <xsl:document href="{$outfile}">
      <xsl:apply-templates select="document('html/page.html')/*">
        <xsl:with-param name="source" select="."/>
        <xsl:with-param name="root" select="/"/>
      </xsl:apply-templates>
    </xsl:document>
  </xsl:template>

  <xsl:template match="//body">
    <xsl:param name="source" />
    <xsl:param name="root"/>
    
    <xsl:element name="{name()}">
      <xsl:apply-templates select="@*"/>

      <xsl:apply-templates select="document('html/navbar.html')/*">
        <xsl:with-param name="source" select="$source" />
        <xsl:with-param name="root" select="$root"/>
      </xsl:apply-templates>
      
      <xsl:apply-templates select="* | text()">
        <xsl:with-param name="source" select="$source"/>
      </xsl:apply-templates>
    </xsl:element>
  </xsl:template>
  
  <xsl:template match="div[@class='navbar-start']">
    <xsl:param name="source"/>
    <xsl:param name="root"/>
    <xsl:element name="{name()}">
      <xsl:apply-templates select="* | @* | text()">
        <xsl:with-param name="source" select="$source"/>
      </xsl:apply-templates>

      <xsl:for-each select="$root//docpages/file[@filestem!='index']">
        <div class="navbar-start">
            <a href="/{./@filestem}.html" class="navbar-item">
              <xsl:value-of select="markdown/metadata/title"/>
            </a>
        </div>
      </xsl:for-each>
    </xsl:element>
  </xsl:template>
  
  <xsl:template match="head/title">
    <xsl:param name="source"/>
    <xsl:element name="{name()}">
      <xsl:apply-templates select="@*"/>
      <xsl:value-of select="$source/markdown/metadata/title"/>
    </xsl:element>
  </xsl:template>
  
  <xsl:template match="h1[@class='title']">
    <xsl:param name="source"/>
    <xsl:element name="{name()}">
      <xsl:apply-templates select="@*"/>
      <xsl:value-of select="$source/markdown/metadata/title"/>
    </xsl:element>
  </xsl:template>
  
  <xsl:template match="h2[@class='subtitle']">
    <xsl:param name="source"/>
    
    <xsl:if test="$source/markdown/metadata/subtitle">
     <xsl:element name="{name()}">
       <xsl:apply-templates select="@*"/>
       <xsl:value-of select="$source/markdown/metadata/subtitle"/>
     </xsl:element>
    </xsl:if>
  </xsl:template>
  
  <xsl:template match="section[@id='pagebody']">
    <xsl:param name="source"/>
    <xsl:element name="{name()}">
      <xsl:apply-templates select="@*"/>
      <xsl:apply-templates select="$source/markdown/html/*"/>
    </xsl:element>
  </xsl:template>
  

  <xsl:template match="//*">
    <xsl:param name="source"/>
    <xsl:param name="root"/>
    <xsl:element name="{name()}">
      <xsl:apply-templates select="* | @* | text()">
        <xsl:with-param name="source" select="$source"/>
        <xsl:with-param name="root" select="$root"/>
      </xsl:apply-templates>
    </xsl:element>
  </xsl:template>

  <xsl:template match="//@*">
    <xsl:attribute name="{name(.)}">
      <xsl:value-of select="."/>
    </xsl:attribute>
  </xsl:template>
</xsl:stylesheet>