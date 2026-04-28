terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# ── Resource Group ─────────────────────────────────────────
resource "azurerm_resource_group" "taskflow" {
  name     = var.resource_group_name
  location = var.location
}

# ── Réseau ─────────────────────────────────────────────────
resource "azurerm_virtual_network" "taskflow" {
  name                = "taskflow-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.taskflow.location
  resource_group_name = azurerm_resource_group.taskflow.name
}

resource "azurerm_subnet" "taskflow" {
  name                 = "taskflow-subnet"
  resource_group_name  = azurerm_resource_group.taskflow.name
  virtual_network_name = azurerm_virtual_network.taskflow.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "taskflow" {
  name                = "taskflow-public-ip"
  location            = azurerm_resource_group.taskflow.location
  resource_group_name = azurerm_resource_group.taskflow.name
  allocation_method   = "Static"
}

# ── Firewall (NSG) ─────────────────────────────────────────
resource "azurerm_network_security_group" "taskflow" {
  name                = "taskflow-nsg"
  location            = azurerm_resource_group.taskflow.location
  resource_group_name = azurerm_resource_group.taskflow.name

  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "App"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Grafana"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3000"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "Prometheus"
    priority                   = 1004
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "9090"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface" "taskflow" {
  name                = "taskflow-nic"
  location            = azurerm_resource_group.taskflow.location
  resource_group_name = azurerm_resource_group.taskflow.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.taskflow.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.taskflow.id
  }
}

resource "azurerm_network_interface_security_group_association" "taskflow" {
  network_interface_id      = azurerm_network_interface.taskflow.id
  network_security_group_id = azurerm_network_security_group.taskflow.id
}

# ── VM Ubuntu ──────────────────────────────────────────────
resource "azurerm_linux_virtual_machine" "taskflow" {
  name                = "taskflow-vm"
  resource_group_name = azurerm_resource_group.taskflow.name
  location            = azurerm_resource_group.taskflow.location
  size                = var.vm_size
  admin_username      = var.admin_username

  network_interface_ids = [azurerm_network_interface.taskflow.id]

  admin_ssh_key {
    username   = var.admin_username
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }
}
