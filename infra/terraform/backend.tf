# ─────────────────────────────────────────────────────────────
# backend.tf — State Terraform distant (Azure Blob Storage)
#
# Prérequis : créer le storage account UNE seule fois manuellement :
#   az group create -n tfstate-rg -l westeurope
#   az storage account create -n taskflowtfstate -g tfstate-rg \
#     --sku Standard_LRS --min-tls-version TLS1_2
#   az storage container create -n tfstate \
#     --account-name taskflowtfstate
#
# Variables via secrets CI (ARM_*) ou az login local.
# ─────────────────────────────────────────────────────────────
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "taskflowtfstate"
    container_name       = "tfstate"
    key                  = "taskflow.terraform.tfstate"
  }
}
