// ── Azure Container Instance deployment ──────────────────────────────────────
// Deploy: az deployment group create --resource-group <rg> --template-file azure-deploy.bicep
// ─────────────────────────────────────────────────────────────────────────────

@description('Name prefix for all resources')
param appName string = 'docusummarize'

@description('Azure region')
param location string = resourceGroup().location

@description('Container image (e.g. your ACR image)')
param containerImage string = 'docusummarize:latest'

@description('Gemini API key (stored as secure env var)')
@secure()
param geminiApiKey string

@description('Number of CPU cores for the container')
param cpuCores int = 1

@description('Memory in GB for the container')
param memoryGB int = 2

// ── Container Group ───────────────────────────────────────────────────────────
resource containerGroup 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: '${appName}-cg'
  location: location
  properties: {
    osType: 'Linux'
    restartPolicy: 'Always'
    ipAddress: {
      type: 'Public'
      ports: [
        { protocol: 'TCP', port: 8501 }
      ]
      dnsNameLabel: appName
    }
    containers: [
      {
        name: appName
        properties: {
          image: containerImage
          ports: [{ port: 8501 }]
          resources: {
            requests: {
              cpu: cpuCores
              memoryInGB: memoryGB
            }
          }
          environmentVariables: [
            {
              name: 'GEMINI_API_KEY'
              secureValue: geminiApiKey
            }
            {
              name: 'OLLAMA_URL'
              value: 'http://localhost:11434'
            }
          ]
        }
      }
    ]
  }
}

output appUrl string = 'http://${containerGroup.properties.ipAddress.fqdn}:8501'
