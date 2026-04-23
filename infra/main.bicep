@description('Environment name')
param environment string = 'dev'

@description('Azure region')
param location string = resourceGroup().location

@description('Unique suffix')
param uniqueSuffix string = uniqueString(resourceGroup().id)

var prefix = 'dociq'
var storageAccountName = '${prefix}stor${uniqueSuffix}'
var keyVaultName = '${prefix}kv${uniqueSuffix}'
var functionAppName = '${prefix}-func-${environment}-${uniqueSuffix}'
var appInsightsName = '${prefix}-insights-${environment}'
var hostingPlanName = '${prefix}-plan-${environment}'
var documentIntelligenceName = '${prefix}-docai-${environment}'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    supportsHttpsTrafficOnly: true
  }
}

// Blob Service
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

// Containers
resource uploadsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'uploads'
  properties: { publicAccess: 'None' }
}

resource processedContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'processed'
  properties: { publicAccess: 'None' }
}

resource resultsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'results'
  properties: { publicAccess: 'None' }
}

// Key Vault
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// App Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: { Application_Type: 'web' }
}

// Hosting Plan (Consumption)
resource hostingPlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: hostingPlanName
  location: location
  sku: { name: 'Y1', tier: 'Dynamic' }
  properties: {}
}

// Function App
resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp'
  identity: { type: 'SystemAssigned' }
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      pythonVersion: '3.11'
      appSettings: [
        { name: 'AzureWebJobsStorage', value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccount.name};EndpointSuffix=${az.environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}' }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        { name: 'APPINSIGHTS_INSTRUMENTATIONKEY', value: appInsights.properties.InstrumentationKey }
        { name: 'KEY_VAULT_URL', value: keyVault.properties.vaultUri }
        { name: 'STORAGE_ACCOUNT_NAME', value: storageAccount.name }
        { name: 'DOCUMENT_INTELLIGENCE_ENDPOINT', value: documentIntelligence.properties.endpoint }
        { name: 'ENVIRONMENT', value: environment }
      ]
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
    }
    httpsOnly: true
  }
}

// Document Intelligence
resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: documentIntelligenceName
  location: location
  kind: 'FormRecognizer'
  sku: { name: 'F0' }
  properties: { publicNetworkAccess: 'Enabled' }
}

// RBAC: Function → Key Vault
resource kvRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionApp.id, 'kv-secrets-user')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// Outputs
output storageAccountName string = storageAccount.name
output keyVaultUrl string = keyVault.properties.vaultUri
output functionAppName string = functionApp.name
output documentIntelligenceEndpoint string = documentIntelligence.properties.endpoint
output functionAppPrincipalId string = functionApp.identity.principalId