Feature: Install an errata to the client

  Scenario: Install an errata to the client
    Given I am on the Systems overview page of this client
     And I follow "Software" in class "content-nav"
     And I follow "Errata" in class "contentnav-row2"
    When I check "slessp1-suseRegister-2953-channel-" in the list 
     And I click on "Apply Errata"
     And I click on "Confirm"
     And I run rhn_check on this client
    Then I should see a "1 errata update has been scheduled for" text
     And "suseRegister-1.4-1.9.1" is installed
