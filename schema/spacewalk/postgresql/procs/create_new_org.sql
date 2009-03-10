--
-- Copyright (c) 2008 Red Hat, Inc.
--
-- This software is licensed to you under the GNU General Public License,
-- version 2 (GPLv2). There is NO WARRANTY for this software, express or
-- implied, including the implied warranties of MERCHANTABILITY or FITNESS
-- FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
-- along with this software; if not, see
-- http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
-- 
-- Red Hat trademarks are not licensed under GPLv2. No permission is
-- granted to use or replicate Red Hat trademarks that are incorporated
-- in this software or its documentation. 
--
--
-- $Id: create_new_org.sql 118829 2007-08-03 00:04:50Z mmccune $
--
--

create or replace function create_new_org
(
        name_in      in varchar,
        password_in  in varchar
        --org_id_out   out number
) returns numeric
as
$$
declare
        ug_type                 numeric;
        group_val               numeric;
        new_org_id              numeric;
        org_id_out		numeric;
begin

        select nextval('web_customer_id_seq') into new_org_id;

        insert into web_customer (
                id, name,
                oracle_customer_id, oracle_customer_number,
                customer_type
        ) values (
                new_org_id, name_in,
                new_org_id, new_org_id, 'B'
        );

        select nextval('rhn_user_group_id_seq') into group_val;

        select  id
        into    ug_type
        from    rhnUserGroupType
        where   label = 'org_admin';

        insert into rhnUserGroup (
                id, name,
                description,
                max_members, group_type, org_id
        ) values (
                group_val, 'Organization Administrators',
                'Organization Administrators for Org ' || name_in,
                NULL, ug_type, new_org_id
        );

        select nextval('rhn_user_group_id_seq') into group_val;

        select  id
        into    ug_type
        from    rhnUserGroupType
        where   label = 'org_applicant';

        insert into rhnUserGroup (
                id, name,
                description,
                max_members, group_type, org_id
        ) VALues (
                group_val, 'Organization Applicants',
                'Organization Applicants for Org ' || name_in,
                NULL, ug_type, new_org_id
        );

        select nextval('rhn_user_group_id_seq') into group_val;

        select  id
        into    ug_type
        from    rhnUserGroupType
        where   label = 'system_group_admin';

        insert into rhnUserGroup (
                id, name,
                description,
                max_members, group_type, org_id
        ) values (
                group_val, 'System Group Administrators',
                'System Group Administrators for Org ' || name_in,
                NULL, ug_type, new_org_id
        );


        select nextval('rhn_user_group_id_seq') into group_val;

        select  id
        into    ug_type
        from    rhnUserGroupType
        where   label = 'activation_key_admin';

        insert into rhnUserGroup (
                id, name,
                description,
                max_members, group_type, org_id
        ) values (
                group_val, 'Activation Key Administrators',
                'Activation Key Administrators for Org ' || name_in,
                NULL, ug_type, new_org_id
        );

        -- config admin is special; it gets created in
        -- rhn_entitlements.set_customer_provisioning instead.

        select nextval('rhn_user_group_id_seq') into group_val;

        select  id
        into    ug_type
        from    rhnUserGroupType
        where   label = 'channel_admin';

        insert into rhnUserGroup (
                id, name,
                description,
                max_members, group_type, org_id
        ) values (
                group_val, 'Channel Administrators',
                'Channel Administrators for Org ' || name_in,
                NULL, ug_type, new_org_id
        );

        -- there aren't any users yet, so we don't need to update
        -- rhnUserServerPerms
        insert into rhnServerGroup
                ( id, name, description, max_members, group_type, org_id )
                select rhn_server_group_id_seq.nextval, sgt.name, sgt.name,
                        0, sgt.id, new_org_id
                from rhnServerGroupType sgt
                where sgt.label = 'sw_mgr_entitled';

        org_id_out := new_org_id;

	-- Returning the value of OUT parameter
        return org_id_out;

end;
$$
language plpgsql;


